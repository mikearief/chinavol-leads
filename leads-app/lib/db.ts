import { Query } from "appwrite";
import { collections, requireServerEnv } from "@/lib/appwrite";
import type {
  LeadLagHistory,
  LeadsUser,
  Monitor,
  MonitorSummary,
  PerformanceRow,
  Signal,
} from "@/types";

interface AppwriteList<T> {
  total: number;
  documents: T[];
}

type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue };

function queryString(queries: string[] = []) {
  const params = new URLSearchParams();
  queries.forEach((query) => params.append("queries[]", query));
  return params.toString() ? `?${params.toString()}` : "";
}

async function appwriteFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const { endpoint, projectId, apiKey } = requireServerEnv();
  const response = await fetch(`${endpoint}/v1${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-Appwrite-Project": projectId,
      "X-Appwrite-Key": apiKey,
      ...init.headers,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Appwrite ${response.status}: ${body}`);
  }

  return (await response.json()) as T;
}

function collectionPath(collectionId: string) {
  const { databaseId } = requireServerEnv();
  return `/databases/${databaseId}/collections/${collectionId}/documents`;
}

export async function listDocuments<T>(
  collectionId: string,
  queries: string[] = [],
): Promise<T[]> {
  const result = await appwriteFetch<AppwriteList<T>>(
    `${collectionPath(collectionId)}${queryString(queries)}`,
  );
  return result.documents;
}

export async function getDocument<T>(
  collectionId: string,
  documentId: string,
): Promise<T | null> {
  try {
    return await appwriteFetch<T>(`${collectionPath(collectionId)}/${documentId}`);
  } catch (error) {
    if (String(error).includes("Appwrite 404")) return null;
    throw error;
  }
}

export async function createDocument<T>(
  collectionId: string,
  documentId: string,
  data: Record<string, JsonValue>,
): Promise<T> {
  return appwriteFetch<T>(collectionPath(collectionId), {
    method: "POST",
    body: JSON.stringify({ documentId, data }),
  });
}

export async function updateDocument<T>(
  collectionId: string,
  documentId: string,
  data: Record<string, JsonValue>,
): Promise<T> {
  return appwriteFetch<T>(`${collectionPath(collectionId)}/${documentId}`, {
    method: "PATCH",
    body: JSON.stringify({ data }),
  });
}

export async function getUserById(userId: string) {
  return getDocument<LeadsUser>(collections.users, userId);
}

export async function getOrCreateUser(input: {
  userId: string;
  email: string;
  username?: string | null;
}) {
  const existing = await getUserById(input.userId);
  if (existing) return existing;

  const byEmail = await listDocuments<LeadsUser>(collections.users, [
    Query.equal("email", input.email),
    Query.limit(1),
  ]);

  if (byEmail[0]) return byEmail[0];

  return createDocument<LeadsUser>(collections.users, input.userId, {
    username: input.username || input.email.split("@")[0],
    email: input.email,
    role: "member",
    approved: false,
    last_login: null,
  });
}

export async function recordLastLogin(userId: string) {
  return updateDocument<LeadsUser>(collections.users, userId, {
    last_login: new Date().toISOString(),
  });
}

export async function listUsers() {
  return listDocuments<LeadsUser>(collections.users, [
    Query.orderAsc("username"),
    Query.limit(100),
  ]);
}

export async function setUserApproval(userId: string, approved: boolean) {
  return updateDocument<LeadsUser>(collections.users, userId, { approved });
}

export async function listActiveMonitors(): Promise<MonitorSummary[]> {
  const monitors = await listDocuments<Monitor>(collections.monitors, [
    Query.equal("active", true),
    Query.orderAsc("ticker"),
    Query.limit(100),
  ]);

  return Promise.all(
    monitors.map(async (monitor) => {
      const [latestLeadLag] = await listDocuments<LeadLagHistory>(
        collections.leadLagHistory,
        [
          Query.equal("monitor_id", monitor.$id),
          Query.orderDesc("computed_at"),
          Query.limit(1),
        ],
      );
      return { ...monitor, latestLeadLag: latestLeadLag ?? null };
    }),
  );
}

export async function getMonitorWithHistory(id: string) {
  const monitor = await getDocument<Monitor>(collections.monitors, id);
  if (!monitor) return null;

  const [history, signals] = await Promise.all([
    listDocuments<LeadLagHistory>(collections.leadLagHistory, [
      Query.equal("monitor_id", id),
      Query.orderAsc("computed_at"),
      Query.limit(60),
    ]),
    listSignals({ monitorId: id, limit: 20 }),
  ]);

  return { monitor, history, signals };
}

export async function listSignals({
  monitorId,
  status,
  limit = 100,
}: {
  monitorId?: string;
  status?: string;
  limit?: number;
} = {}): Promise<Signal[]> {
  const queries = [Query.orderDesc("signal_ts"), Query.limit(limit)];
  if (monitorId) queries.unshift(Query.equal("monitor_id", monitorId));
  if (status) queries.unshift(Query.equal("status", status));

  const signals = await listDocuments<Signal>(collections.signals, queries);
  const monitorIds = [...new Set(signals.map((signal) => signal.monitor_id))];
  const monitors = await Promise.all(
    monitorIds.map((id) => getDocument<Monitor>(collections.monitors, id)),
  );
  const monitorById = new Map(
    monitors.filter(Boolean).map((monitor) => [monitor!.$id, monitor!]),
  );

  return signals.map((signal) => ({
    ...signal,
    monitor: monitorById.get(signal.monitor_id),
  }));
}

export async function getSignalPerformance(): Promise<PerformanceRow[]> {
  const signals = await listSignals({ status: "resolved", limit: 500 });
  const grouped = new Map<string, PerformanceRow>();

  for (const signal of signals) {
    const monitor = signal.monitor;
    const key = signal.monitor_id;
    const direction = signal.direction === "UP" ? 1 : -1;
    const oneHour = signal.outcome_at_1h ?? 0;
    const signed = oneHour * direction;
    const current = grouped.get(key) ?? {
      monitor_id: key,
      ticker: monitor?.ticker ?? key,
      slug: monitor?.slug ?? key,
      n_signals: 0,
      n_wins: 0,
      avg_return: 0,
      gross_pnl: 0,
    };

    current.n_signals += 1;
    current.n_wins += signed > 0 ? 1 : 0;
    current.gross_pnl += signed;
    current.avg_return =
      ((current.avg_return ?? 0) * (current.n_signals - 1) + oneHour) /
      current.n_signals;
    grouped.set(key, current);
  }

  return [...grouped.values()];
}
