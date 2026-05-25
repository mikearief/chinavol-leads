import { getCurrentSession } from "@/lib/session";
import Link from "next/link";
import { redirect } from "next/navigation";

export default async function PendingPage() {
  const session = await getCurrentSession();
  if (!session) redirect("/login");
  if (session.user.approved) redirect("/dashboard");

  return (
    <div className="auth-box pending-box">
      <h1>Access Pending</h1>
      <p>Your request is waiting for Mike&apos;s approval. You&apos;ll be able to use the leads dashboard once approved.</p>
      <Link href="/login">Back to login</Link>
    </div>
  );
}
