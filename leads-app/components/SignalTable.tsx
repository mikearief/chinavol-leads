import type { Signal } from "@/types";

function fmtDate(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function fmtNumber(value?: number | null, digits = 1) {
  return typeof value === "number" ? value.toFixed(digits) : "-";
}

export function SignalTable({ signals }: { signals: Signal[] }) {
  return (
    <div className="signals-table-wrapper">
      <table className="signals-table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Ticker</th>
            <th>Direction</th>
            <th>PM Move</th>
            <th>Confidence</th>
            <th>Status</th>
            <th>1h</th>
            <th>4h</th>
          </tr>
        </thead>
        <tbody>
          {signals.map((signal) => (
            <tr key={signal.$id}>
              <td>{fmtDate(signal.signal_ts)}</td>
              <td>{signal.monitor?.ticker ?? signal.monitor_id}</td>
              <td>
                <span className={`direction ${signal.direction.toLowerCase()}`}>
                  {signal.direction}
                </span>
              </td>
              <td>{fmtNumber(signal.pm_move_pp, 2)} pp</td>
              <td>{signal.confidence}</td>
              <td>{signal.status}</td>
              <td>{fmtNumber(signal.outcome_at_1h)}</td>
              <td>{fmtNumber(signal.outcome_at_4h)}</td>
            </tr>
          ))}
          {!signals.length && (
            <tr>
              <td colSpan={8} className="empty-cell">
                No signals yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
