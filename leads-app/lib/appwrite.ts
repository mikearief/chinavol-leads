import { Account, Client, Databases } from "appwrite";

export const appwriteEndpoint =
  process.env.NEXT_PUBLIC_APPWRITE_ENDPOINT ?? "https://aw.smartpiggies.cloud";

export const appwriteProjectId =
  process.env.NEXT_PUBLIC_APPWRITE_PROJECT_ID ?? "6a14aeb7001912f0717c";

export const appwriteDatabaseId = process.env.APPWRITE_DATABASE_ID ?? "";

export const collections = {
  users: process.env.APPWRITE_USERS_COLLECTION_ID ?? "leads_users",
  monitors: process.env.APPWRITE_MONITORS_COLLECTION_ID ?? "leads_monitors",
  signals: process.env.APPWRITE_SIGNALS_COLLECTION_ID ?? "leads_signals",
  leadLagHistory:
    process.env.APPWRITE_LEAD_LAG_COLLECTION_ID ?? "leads_lead_lag_history",
} as const;

export function createBrowserClient() {
  return new Client().setEndpoint(appwriteEndpoint).setProject(appwriteProjectId);
}

export function createBrowserAccount() {
  return new Account(createBrowserClient());
}

export function createBrowserDatabases() {
  return new Databases(createBrowserClient());
}

export function requireServerEnv() {
  const apiKey = process.env.APPWRITE_API_KEY;

  if (!appwriteEndpoint || !appwriteProjectId || !appwriteDatabaseId || !apiKey) {
    throw new Error(
      "Missing Appwrite configuration. Set NEXT_PUBLIC_APPWRITE_ENDPOINT, NEXT_PUBLIC_APPWRITE_PROJECT_ID, APPWRITE_DATABASE_ID, and APPWRITE_API_KEY.",
    );
  }

  return {
    endpoint: appwriteEndpoint.replace(/\/$/, ""),
    projectId: appwriteProjectId,
    databaseId: appwriteDatabaseId,
    apiKey,
  };
}
