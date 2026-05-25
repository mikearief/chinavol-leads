"""Flask-Login user class and AppWrite auth helpers."""

import requests
from flask_login import UserMixin, LoginManager
from .config import Config
from .db import query_one

login_manager = LoginManager()


class LeadsUser(UserMixin):
    def __init__(self, row: dict):
        self.id = row['id']
        self.appwrite_uid = row.get('appwrite_uid')
        self.username = row['username']
        self.email = row['email']
        self.role = row['role']
        self.approved = bool(row['approved'])
        self.approved_by = row.get('approved_by')
        self.approved_at = row.get('approved_at')
        self.created_at = row['created_at']
        self.last_login = row.get('last_login')

    def is_approved(self) -> bool:
        return self.approved or self.role == 'admin'

    def is_admin(self) -> bool:
        return self.role == 'admin'


@login_manager.user_loader
def load_user(user_id):
    row = query_one("SELECT * FROM leads_users WHERE id = ?", (user_id,))
    return LeadsUser(row) if row else None


def fetch_appwrite_user(jwt: str) -> dict | None:
    """Call AppWrite /v1/account to get current user from JWT cookie."""
    if not Config.APPWRITE_URL or not Config.APPWRITE_PROJECT_ID:
        return None
    try:
        resp = requests.get(
            f"{Config.APPWRITE_URL}/v1/account",
            headers={
                "X-Appwrite-Project": Config.APPWRITE_PROJECT_ID,
                "X-Appwrite-JWT": jwt,
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def create_appwrite_session(email: str, password: str) -> str | None:
    """Create email+password session in AppWrite and return JWT."""
    if not Config.APPWRITE_URL or not Config.APPWRITE_PROJECT_ID:
        return None
    try:
        resp = requests.post(
            f"{Config.APPWRITE_URL}/v1/account/sessions/email",
            headers={"X-Appwrite-Project": Config.APPWRITE_PROJECT_ID, "Content-Type": "application/json"},
            json={"email": email, "password": password},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("providerAccessToken") or data.get("secret")
    except Exception as exc:
        return None


def get_or_create_local_user(appwrite_uid: str, email: str, username: str) -> LeadsUser | None:
    row = query_one("SELECT * FROM leads_users WHERE appwrite_uid = ?", (appwrite_uid,))
    if not row:
        row = query_one("SELECT * FROM leads_users WHERE email = ?", (email,))
    if not row:
        # Auto-create local row with pending approval
        from .db import execute
        execute(
            """INSERT INTO leads_users (appwrite_uid, username, email, role, approved)
               VALUES (?, ?, ?, 'member', 0)""",
            (appwrite_uid, username, email),
        )
        row = query_one("SELECT * FROM leads_users WHERE appwrite_uid = ?", (appwrite_uid,))
    return LeadsUser(row) if row else None


def approved_required(f):
    """Decorator to require approved user (admin bypasses). Returns 403 for API use."""
    from functools import wraps
    from flask import abort
    from flask_login import current_user

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_approved', lambda: False)():
            abort(403)
        return f(*args, **kwargs)
    return decorated
