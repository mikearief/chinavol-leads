import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { listSignals } from "@/lib/db";

export async function GET(request: Request) {
  const session = await getServerSession(authOptions);
  if (!session?.user.approved) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const signals = await listSignals({
    monitorId: searchParams.get("monitor_id") ?? undefined,
    status: searchParams.get("status") ?? undefined,
  });

  return NextResponse.json({ signals });
}
