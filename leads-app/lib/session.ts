import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";
import { authOptions } from "@/lib/auth";

export async function getCurrentSession() {
  return getServerSession(authOptions);
}

export async function requireApprovedSession() {
  const session = await getCurrentSession();
  if (!session) redirect("/login");
  if (!session.user.approved) redirect("/pending");
  return session;
}

export async function requireAdminSession() {
  const session = await requireApprovedSession();
  if (session.user.role !== "admin") redirect("/dashboard");
  return session;
}
