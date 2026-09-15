import { createContext } from "react";

import type { AuthStatus, AuthUser, SignupPayload } from "../types/auth";

export type AuthContextValue = {
  user: AuthUser | null;
  status: AuthStatus;
  isAuthenticated: boolean;
  loginError: string | null;
  refreshUser: () => Promise<void>;
  login: (username: string, password: string) => Promise<void>;
  signup: (payload: SignupPayload) => Promise<void>;
  logout: () => Promise<void>;
};

export const AuthContext = createContext<AuthContextValue | null>(null);