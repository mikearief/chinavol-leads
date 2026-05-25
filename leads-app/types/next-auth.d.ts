import type { DefaultSession } from "next-auth";
import type { JWT as DefaultJWT } from "next-auth/jwt";
import type { UserRole } from "./index";

declare module "next-auth" {
  interface Session {
    user: {
      userId: string;
      username: string;
      role: UserRole;
      approved: boolean;
    } & DefaultSession["user"];
  }

  interface User {
    userId: string;
    username: string;
    role: UserRole;
    approved: boolean;
  }
}

declare module "next-auth/jwt" {
  interface JWT extends DefaultJWT {
    userId: string;
    username: string;
    role: UserRole;
    approved: boolean;
  }
}
