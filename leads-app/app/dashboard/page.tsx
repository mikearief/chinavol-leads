import { MonitorCard } from "@/components/MonitorCard";
import { listActiveMonitors } from "@/lib/db";
import { requireApprovedSession } from "@/lib/session";

export default async function DashboardPage() {
  await requireApprovedSession();
  const monitors = await listActiveMonitors();

  return (
    <>
      <div className="page-header">
        <h1>PM Market Monitor</h1>
        <p className="subtitle">Polymarket to equity lead/lag signals</p>
      </div>

      <div className="monitors-grid">
        {monitors.map((monitor) => (
          <MonitorCard key={monitor.$id} monitor={monitor} />
        ))}
        {!monitors.length && (
          <div className="empty-state">
            <p>No monitors configured.</p>
          </div>
        )}
      </div>
    </>
  );
}
