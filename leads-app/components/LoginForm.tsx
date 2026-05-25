"use client";

import { useState, useTransition } from "react";
import { signIn } from "next-auth/react";
import { useRouter, useSearchParams } from "next/navigation";

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState("");
  const [isPending, startTransition] = useTransition();

  function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    const formData = new FormData(event.currentTarget);
    const email = String(formData.get("email") ?? "");
    const password = String(formData.get("password") ?? "");
    const callbackUrl = searchParams.get("callbackUrl") || "/dashboard";

    startTransition(async () => {
      const result = await signIn("credentials", {
        email,
        password,
        redirect: false,
        callbackUrl,
      });

      if (result?.error) {
        setError("Invalid email or password.");
        return;
      }

      router.push(result?.url ?? callbackUrl);
      router.refresh();
    });
  }

  return (
    <form onSubmit={onSubmit}>
      {error && <div className="alert alert-error">{error}</div>}
      <div className="form-group">
        <label htmlFor="email">Email</label>
        <input id="email" name="email" type="email" required autoFocus />
      </div>
      <div className="form-group">
        <label htmlFor="password">Password</label>
        <input id="password" name="password" type="password" required />
      </div>
      <button type="submit" className="btn btn-primary" disabled={isPending}>
        {isPending ? "Logging in..." : "Log in"}
      </button>
    </form>
  );
}
