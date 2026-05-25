import type { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { appwriteEndpoint, appwriteProjectId } from "@/lib/appwrite";
import { getOrCreateUser, recordLastLogin } from "@/lib/db";

interface AppwriteSessionResponse {
  userId: string;
}

async function createAppwriteEmailSession(email: string, password: string) {
  const response = await fetch(
    `${appwriteEndpoint.replace(/\/$/, "")}/v1/account/sessions/email`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Appwrite-Project": appwriteProjectId,
      },
      body: JSON.stringify({ email, password }),
      cache: "no-store",
    },
  );

  if (!response.ok) return null;
  return (await response.json()) as AppwriteSessionResponse;
}

export const authOptions: NextAuthOptions = {
  session: {
    strategy: "jwt",
  },
  pages: {
    signIn: "/login",
  },
  providers: [
    CredentialsProvider({
      name: "Appwrite",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        const email = credentials?.email?.trim().toLowerCase();
        const password = credentials?.password;
        if (!email || !password) return null;

        const appwriteSession = await createAppwriteEmailSession(email, password);
        if (!appwriteSession?.userId) return null;

        const leadsUser = await getOrCreateUser({
          userId: appwriteSession.userId,
          email,
        });

        if (leadsUser.approved || leadsUser.role === "admin") {
          await recordLastLogin(leadsUser.$id);
        }

        return {
          id: leadsUser.$id,
          userId: leadsUser.$id,
          name: leadsUser.username,
          email: leadsUser.email,
          username: leadsUser.username,
          role: leadsUser.role,
          approved: leadsUser.approved || leadsUser.role === "admin",
        };
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.userId = user.userId;
        token.username = user.username;
        token.role = user.role;
        token.approved = user.approved;
      }
      return token;
    },
    async session({ session, token }) {
      session.user.userId = token.userId;
      session.user.username = token.username;
      session.user.role = token.role;
      session.user.approved = token.approved;
      return session;
    },
  },
};
