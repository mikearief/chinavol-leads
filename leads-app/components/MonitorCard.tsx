import Link from "next/link";
import type { MonitorSummary } from "@/types";

function minutes(seconds: number) {
  return Math.round(Math.abs(seconds) / 60);
}

export function MonitorCard({ monitor }: { monitor: MonitorSummary }) {
  const latest = monitor.latestLeadLag;

  return (
    <article className="monitor-card">
      <div className="card-header">
        <h3 className="ticker">{monitor.ticker}</h3>
        <span className={`badge ${monitor.active ? "badge-active" : "badge-inactive"}`}>
          {monitor.active ? "Active" : "Inactive"}
        </span>
      </div>

      <div className="card-body">
        <p className="pm-question">{monitor.pm_question || monitor.slug}</p>
        <div className="stat-row">
          <div className="stat">
            <span className="stat-label">Threshold</span>
            <span className="stat-value">{monitor.signal_thresh_pp} pp</span>
          </div>
          <div className="stat">
            <span className="stat-label">Cooldown</span>
            <span className="stat-value">{monitor.cooldown_hrs} hrs</span>
          </div>
        </div>
        <p className="description">{monitor.description ?? ""}</p>
        {latest ? (
          <div className="stat-row compact">
            <div className="stat">
              <span className="stat-label">Lead</span>
              <span className="stat-value">{minutes(latest.lead_seconds)}m</span>
            </div>
            <div className="stat">
              <span className="stat-label">Lag</span>
              <span className="stat-value">{minutes(latest.lag_seconds)}m</span>
            </div>
            <div className="stat">
              <span className="stat-label">Corr</span>
              <span className="stat-value">{latest.correlation.toFixed(3)}</span>
            </div>
          </div>
        ) : (
          <p className="lead-lag-placeholder">
            No lead/lag data yet - running first computation
          </p>
        )}
      </div>

      <div className="card-footer">
        <Link className="btn btn-sm" href={`/monitor/${monitor.$id}`}>
          Details
        </Link>
      </div>
    </article>
  );
}
