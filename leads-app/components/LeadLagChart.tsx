"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { LeadLagHistory } from "@/types";

function chartDate(value: string) {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
  }).format(new Date(value));
}

export function LeadLagChart({ history }: { history: LeadLagHistory[] }) {
  if (!history.length) {
    return <p className="placeholder">No lead/lag data yet - running first computation.</p>;
  }

  const data = history.map((row) => ({
    time: chartDate(row.computed_at),
    leadMinutes: Math.round(row.lead_seconds / 60),
    lagMinutes: Math.round(row.lag_seconds / 60),
    correlation: Number(row.correlation.toFixed(3)),
  }));

  return (
    <div className="chart-shell">
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
          <CartesianGrid stroke="#334155" strokeDasharray="3 3" />
          <XAxis dataKey="time" stroke="#94a3b8" tick={{ fontSize: 12 }} />
          <YAxis yAxisId="seconds" stroke="#f59e0b" tick={{ fontSize: 12 }} />
          <YAxis
            yAxisId="corr"
            orientation="right"
            domain={[-1, 1]}
            stroke="#8b5cf6"
            tick={{ fontSize: 12 }}
          />
          <Tooltip
            contentStyle={{
              background: "#0f172a",
              border: "1px solid #334155",
              borderRadius: 6,
            }}
          />
          <Legend />
          <Line
            yAxisId="seconds"
            type="monotone"
            dataKey="leadMinutes"
            name="Lead minutes"
            stroke="#f59e0b"
            strokeWidth={2}
            dot={false}
          />
          <Line
            yAxisId="seconds"
            type="monotone"
            dataKey="lagMinutes"
            name="Lag minutes"
            stroke="#22c55e"
            strokeWidth={2}
            dot={false}
          />
          <Line
            yAxisId="corr"
            type="monotone"
            dataKey="correlation"
            name="Correlation"
            stroke="#8b5cf6"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
