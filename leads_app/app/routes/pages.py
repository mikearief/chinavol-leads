"""Page routes for leads dashboard, monitor detail, signals pages."""

from flask import Blueprint, render_template, abort, redirect, url_for
from flask_login import login_required, current_user
from ..db import query_all, query_one
from ..models import Monitor

bp = Blueprint('pages', __name__, template_folder='../../templates/leads')


def approved_required(f):
    from functools import wraps
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('leads.auth.login'))
        if not current_user.is_approved():
            return render_template('pending.html')
        return f(*args, **kwargs)
    return wrapped


@bp.route('/')
@login_required
@approved_required
def dashboard():
    rows = query_all("SELECT * FROM leads_monitors WHERE active=1 ORDER BY id")
    monitors = [Monitor.from_row(r) for r in rows]
    return render_template('dashboard.html', monitors=monitors, user=current_user)


@bp.route('/monitor/<int:monitor_id>')
@login_required
@approved_required
def monitor_detail(monitor_id: int):
    row = query_one("SELECT * FROM leads_monitors WHERE id = ?", (monitor_id,))
    if not row:
        abort(404)
    monitor = Monitor.from_row(row)
    latest_ll = query_one(
        "SELECT * FROM leads_lead_lag_history WHERE monitor_id=? ORDER BY computed_at DESC LIMIT 1",
        (monitor_id,)
    )
    signals = query_all(
        "SELECT * FROM leads_signals WHERE monitor_id=? ORDER BY signal_ts DESC LIMIT 20",
        (monitor_id,)
    )
    return render_template('monitor.html', monitor=monitor,
        latest_ll=latest_ll,
        signals=signals,
        user=current_user)


@bp.route('/signals')
@login_required
@approved_required
def signals_page():
    signals = query_all(
        """SELECT s.*, m.ticker, m.slug, m.pm_question
           FROM leads_signals s JOIN leads_monitors m ON s.monitor_id=m.id
           ORDER BY s.signal_ts DESC LIMIT 100"""
    )
    return render_template('signals.html', signals=signals, user=current_user)
