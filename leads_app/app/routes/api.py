"""JSON REST API routes."""

from flask import Blueprint, jsonify, request, abort
from flask_login import login_required, current_user
from ..auth import approved_required
from ..db import query_all, query_one
from ..models import Monitor

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route('/monitors')
@login_required
@approved_required
def list_monitors():
    rows = query_all("SELECT * FROM leads_monitors WHERE active=1 ORDER BY id")
    monitors = [Monitor.from_row(r).__dict__ for r in rows]
    return jsonify(monitors=monitors)


@bp.route('/monitor/<int:monitor_id>')
@login_required
@approved_required
def monitor_detail(monitor_id: int):
    row = query_one("SELECT * FROM leads_monitors WHERE id = ?", (monitor_id,))
    if not row:
        abort(404)
    monitor = Monitor.from_row(row)
    ll = query_all(
        "SELECT * FROM leads_lead_lag_history WHERE monitor_id=? ORDER BY computed_at DESC LIMIT 30",
        (monitor_id,)
    )
    return jsonify(monitor=monitor.__dict__, lead_lag_history=ll)


@bp.route('/signals')
@login_required
@approved_required
def signals():
    monitor_id = request.args.get('monitor_id', type=int)
    status = request.args.get('status', '')
    query = """SELECT s.*, m.ticker FROM leads_signals s
               JOIN leads_monitors m ON s.monitor_id=m.id WHERE 1=1"""
    params = []
    if monitor_id:
        query += ' AND s.monitor_id=?'
        params.append(monitor_id)
    if status:
        query += ' AND s.status=?'
        params.append(status)
    query += ' ORDER BY s.signal_ts DESC LIMIT 100'
    rows = query_all(query, params)
    return jsonify(signals=rows)


@bp.route('/signals/performance')
@login_required
@approved_required
def performance():
    rows = query_all("""
        SELECT monitor_id, m.ticker, m.slug,
               COUNT(*) as n_signals,
               SUM(CASE WHEN outcome_at_1h * (CASE WHEN direction='UP' THEN 1 ELSE -1 END) > 0 THEN 1 ELSE 0 END) as n_wins,
               AVG(outcome_at_1h) as avg_return,
               SUM(outcome_at_1h * (CASE WHEN direction='UP' THEN 1 ELSE -1 END)) as gross_pnl
        FROM leads_signals s JOIN leads_monitors m ON s.monitor_id=m.id
        WHERE s.status = 'resolved'
        GROUP BY monitor_id
    """)
    return jsonify(performance=rows)
