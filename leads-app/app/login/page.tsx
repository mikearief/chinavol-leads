import { getCurrentSession } from "@/lib/session";
import { redirect } from "next/navigation";
import { LoginForm } from "@/components/LoginForm";

export default async function LoginPage() {
  const session = await getCurrentSession();
  if (session?.user.approved) redirect("/dashboard");
  if (session && !session.user.approved) redirect("/pending");

  return (
    <div className="auth-box">
      <h1>Log in</h1>
      <LoginForm />
    </div>
  );
}
