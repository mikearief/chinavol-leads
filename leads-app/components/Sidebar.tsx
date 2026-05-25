"use client";

import Link from "next/link";
import { signOut, useSession } from "next-auth/react";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/signals", label: "Signals" },
  { href: "/admin", label: "Admin", adminOnly: true },
];

export function Sidebar() {
  const pathname = usePathname();
  const { data: session, status } = useSession();
  const isAuthPage = pathname === "/login";

  if (isAuthPage) return null;

  return (
    <aside className="sidebar">
      <Link className="logo" href="/dashboard">
        <span className="logo-mark">CV</span>
        <span className="logo-text">
          ChinaVol<span className="logo-suffix">Pro</span>
        </span>
      </Link>

      <nav className="sidebar-nav" aria-label="Primary">
        {navItems
          .filter((item) => !item.adminOnly || session?.user.role === "admin")
          .map((item) => (
            <Link
              key={item.href}
              className={pathname.startsWith(item.href) ? "active" : ""}
              href={item.href}
            >
              {item.label}
            </Link>
          ))}
      </nav>

      <div className="sidebar-footer">
        {status === "authenticated" ? (
          <>
            <span className="user-badge">{session.user.username}</span>
            <button className="btn btn-sm" onClick={() => signOut({ callbackUrl: "/login" })}>
              Log out
            </button>
          </>
        ) : (
          <Link className="btn btn-sm" href="/login">
            Log in
          </Link>
        )}
      </div>
    </aside>
  );
}
