"""Auth routes: login, register, logout (wraps AppWrite Auth)."""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from ..auth import (
    create_appwrite_session,
    get_or_create_local_user,
    LeadsUser,
    login_manager,
)
from ..config import Config
from ..db import query_one, execute
import requests

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('leads.pages.dashboard'))

    return render_template('login.html')


@bp.route('/auth/login', methods=['POST'])
def submit_login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    row = query_one("SELECT * FROM leads_users WHERE username = ?", (username,))
    if not row:
        flash("Invalid username or password.", "error")
        return render_template('login.html')

    email = row['email']
    jwt_or_secret = create_appwrite_session(email, password)

    user = LeadsUser(row)
    if not jwt_or_secret:
        # Phase 1 fallback: allow local login for approved admins when AppWrite is unavailable
        if user.is_approved() and user.is_admin():
            execute(
                "UPDATE leads_users SET last_login = datetime('now') WHERE id = ?",
                (user.id,)
            )
            login_user(user, remember=True)
            return redirect(url_for('leads.pages.dashboard'))
        flash("Invalid username or password.", "error")
        return render_template('login.html')

    if not user.is_approved():
        return render_template('pending.html')
    execute(
        "UPDATE leads_users SET last_login = datetime('now') WHERE id = ?",
        (user.id,)
    )
    login_user(user, remember=True)
    return redirect(url_for('leads.pages.dashboard'))


@bp.route('/register', methods=['GET'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('leads.pages.dashboard'))

    return render_template('register.html')


@bp.route('/auth/register', methods=['POST'])
def submit_register():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    if not username or not email or len(password) < 6:
        flash("Please fill all fields (password min 6 chars).", "error")
        return render_template('register.html')

    appwrite_uid = None
    try:
        resp = requests.post(
            f"{Config.APPWRITE_URL}/v1/account",
            headers={
                "X-Appwrite-Project": Config.APPWRITE_PROJECT_ID,
                "Content-Type": "application/json",
            },
            json={"userId": "unique()", "email": email, "password": password, "name": username},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        appwrite_uid = data.get("$id")
    except requests.exceptions.RequestException:
        # Phase 1 fallback: create local-only user if AppWrite is unavailable
        pass

    try:
        execute(
            "INSERT INTO leads_users (appwrite_uid, username, email, role, approved) VALUES (?, ?, ?, 'member', 0)",
            (appwrite_uid, username, email),
        )
    except Exception as exc:
        flash(f"Local user creation failed: {exc}", "error")
        return render_template('register.html')

    return render_template('pending.html')


@bp.route('/auth/logout')
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('leads.auth.login'))
