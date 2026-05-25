import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { getSignalPerformance } from "@/lib/db";

export async function GET() {
  const session = await getServerSession(authOptions);
  if (!session?.user.approved) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const performance = await getSignalPerformance();
  return NextResponse.json({ performance });
}
