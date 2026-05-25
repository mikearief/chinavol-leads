import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { listUsers } from "@/lib/db";

export async function GET() {
  const session = await getServerSession(authOptions);
  if (!session?.user.approved || session.user.role !== "admin") {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  const users = await listUsers();
  return NextResponse.json({ users });
}
