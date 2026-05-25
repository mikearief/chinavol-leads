import { SignalTable } from "@/components/SignalTable";
import { listSignals } from "@/lib/db";
import { requireApprovedSession } from "@/lib/session";

export default async function SignalsPage({
  searchParams,
}: {
  searchParams: Promise<{ monitor_id?: string; status?: string }>;
}) {
  await requireApprovedSession();
  const filters = await searchParams;
  const signals = await listSignals({
    monitorId: filters.monitor_id,
    status: filters.status,
  });

  return (
    <>
      <div className="page-header">
        <h1>Signal History</h1>
        <p className="subtitle">All generated signals and outcomes</p>
      </div>

      <form className="filter-bar">
        <div className="form-group compact-field">
          <label htmlFor="status">Status</label>
          <select id="status" name="status" defaultValue={filters.status ?? ""}>
            <option value="">All</option>
            <option value="active">Active</option>
            <option value="pending">Pending</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>
        <button className="btn btn-sm" type="submit">
          Apply
        </button>
      </form>

      <SignalTable signals={signals} />
    </>
  );
}
