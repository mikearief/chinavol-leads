import type { Metadata } from "next";
import "./globals.css";
import { SessionProvider } from "@/components/SessionProvider";
import { Sidebar } from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "ChinaVol Pro Leads",
  description: "Polymarket to equity lead/lag signal monitor",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <SessionProvider>
          <div className="app-shell">
            <Sidebar />
            <main className="main-content">{children}</main>
          </div>
        </SessionProvider>
      </body>
    </html>
  );
}
