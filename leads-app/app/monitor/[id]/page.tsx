import Link from "next/link";
import { notFound } from "next/navigation";
import { LeadLagChart } from "@/components/LeadLagChart";
import { SignalTable } from "@/components/SignalTable";
import { getMonitorWithHistory } from "@/lib/db";
import { requireApprovedSession } from "@/lib/session";

function minutes(seconds: number) {
  return Math.round(Math.abs(seconds) / 60);
}

export default async function MonitorPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  await requireApprovedSession();
  const { id } = await params;
  const detail = await getMonitorWithHistory(id);
  if (!detail) notFound();

  const latest = detail.history.at(-1);

  return (
    <>
      <div className="page-header">
        <Link className="back-link" href="/dashboard">
          Back to Dashboard
        </Link>
        <h1>{detail.monitor.ticker}</h1>
        <p className="subtitle">{detail.monitor.pm_question || detail.monitor.slug}</p>
      </div>

      <div className="detail-grid">
        <section className="detail-panel">
          <h2>Polymarket Probability</h2>
          <p className="placeholder">No PM history available yet.</p>
        </section>
        <section className="detail-panel">
          <h2>Equity Price</h2>
          <p className="placeholder">No equity bars cached yet.</p>
        </section>
      </div>

      <section className="detail-panel">
        <h2>Lead / Lag</h2>
        {latest ? (
          <div className="stat-row lead-lag-stats">
            <div className="stat">
              <span className="stat-label">Lead</span>
              <span className="stat-value">{minutes(latest.lead_seconds)} min</span>
            </div>
            <div className="stat">
              <span className="stat-label">Lag</span>
              <span className="stat-value">{minutes(latest.lag_seconds)} min</span>
            </div>
            <div className="stat">
              <span className="stat-label">Correlation r</span>
              <span className="stat-value">{latest.correlation.toFixed(3)}</span>
            </div>
          </div>
        ) : null}
        <LeadLagChart history={detail.history} />
      </section>

      <section className="detail-panel">
        <h2>Signals</h2>
        <SignalTable signals={detail.signals} />
      </section>
    </>
  );
}
