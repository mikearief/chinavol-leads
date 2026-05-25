export type UserRole = "admin" | "member";
export type SignalDirection = "UP" | "DOWN";
export type SignalConfidence = "LOW" | "MEDIUM" | "HIGH";
export type SignalStatus = "active" | "pending" | "resolved";

export interface AppwriteDocument {
  $id: string;
  $createdAt?: string;
  $updatedAt?: string;
}

export interface LeadsUser extends AppwriteDocument {
  username: string;
  email: string;
  role: UserRole;
  approved: boolean;
  last_login?: string | null;
}

export interface Monitor extends AppwriteDocument {
  slug: string;
  pm_question: string;
  ticker: string;
  description?: string | null;
  signal_thresh_pp: number;
  cooldown_hrs: number;
  active: boolean;
}

export interface LeadLagHistory extends AppwriteDocument {
  monitor_id: string;
  lead_seconds: number;
  lag_seconds: number;
  correlation: number;
  computed_at: string;
}

export interface Signal extends AppwriteDocument {
  monitor_id: string;
  signal_ts: string;
  pm_ts: string;
  pm_prob_before: number;
  pm_prob_after: number;
  pm_move_pp: number;
  direction: SignalDirection;
  predicted_eq_return_bps: number;
  confidence: SignalConfidence;
  status: SignalStatus;
  outcome_at_1h?: number | null;
  outcome_at_4h?: number | null;
  created_at: string;
  monitor?: Pick<Monitor, "$id" | "slug" | "ticker" | "pm_question">;
}

export interface MonitorSummary extends Monitor {
  latestLeadLag?: LeadLagHistory | null;
}

export interface PerformanceRow {
  monitor_id: string;
  ticker: string;
  slug: string;
  n_signals: number;
  n_wins: number;
  avg_return: number | null;
  gross_pnl: number;
}
