import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { getMonitorWithHistory } from "@/lib/db";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const session = await getServerSession(authOptions);
  if (!session?.user.approved) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { id } = await params;
  const detail = await getMonitorWithHistory(id);
  if (!detail) {
    return NextResponse.json({ error: "Monitor not found" }, { status: 404 });
  }

  return NextResponse.json(detail);
}
