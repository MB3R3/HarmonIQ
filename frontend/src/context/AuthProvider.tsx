import { useCallback, useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";

import {
  getCurrentUser,
  loginUser,
  logoutUser,
  signupUser,
} from "../services/auth";
import type {
  AuthStatus,
  AuthUser,
  SessionStatus,
  SignupPayload,
} from "../types/auth";
import { AuthContext } from "./authContext";

type ResolvedSession = {
  user: AuthUser | null;
  status: AuthStatus;
};

function resolveSession(session: SessionStatus): ResolvedSession {
  if (session.authenticated && session.user) {
    return { user: session.user, status: "authenticated" };
  }
  return { user: null, status: "unauthenticated" };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [loginError, setLoginError] = useState<string | null>(null);
  const requestRef = useRef(0);

  const setSession = useCallback((session: SessionStatus) => {
    const next = resolveSession(session);
    setUser(next.user);
    setStatus(next.status);
  }, []);

  const refreshUser = useCallback(async () => {
    const requestId = requestRef.current + 1;
    requestRef.current = requestId;

    try {
      const session = await getCurrentUser();
      if (requestRef.current !== requestId) return;
      setSession(session);
    } catch {
      if (requestRef.current !== requestId) return;
      setUser(null);
      setStatus("unauthenticated");
    }
  }, [setSession]);

  const logout = useCallback(async () => {
    const requestId = requestRef.current + 1;
    requestRef.current = requestId;

    try {
      await logoutUser();
    } catch {
      // Clear local auth state regardless so protected routes react.
    }
    if (requestRef.current !== requestId) return;
    setUser(null);
    setStatus("unauthenticated");
    setLoginError(null);
  }, []);

  const login = useCallback(
    async (username: string, password: string) => {
      const requestId = requestRef.current + 1;
      requestRef.current = requestId;
      setLoginError(null);

      try {
        const session = await loginUser(username, password);
        if (requestRef.current !== requestId) return;
        setSession(session);
      } catch (error) {
        if (requestRef.current !== requestId) return;
        const message =
          error instanceof Error
            ? error.message
            : "Unable to log in. Please try again.";
        setLoginError(message);
        throw error;
      }
    },
    [setSession]
  );

  const signup = useCallback(
    async (payload: SignupPayload) => {
      const requestId = requestRef.current + 1;
      requestRef.current = requestId;
      setLoginError(null);

      try {
        const session = await signupUser(payload);
        if (requestRef.current !== requestId) return;
        setSession(session);
      } catch (error) {
        if (requestRef.current !== requestId) return;
        const message =
          error instanceof Error
            ? error.message
            : "Unable to create your account. Please try again.";
        setLoginError(message);
        throw error;
      }
    },
    [setSession]
  );

  useEffect(() => {
    const requestId = requestRef.current + 1;
    requestRef.current = requestId;

    getCurrentUser()
      .then((session) => {
        if (requestRef.current !== requestId) return;
        setSession(session);
      })
      .catch(() => {
        if (requestRef.current !== requestId) return;
        setUser(null);
        setStatus("unauthenticated");
      });
  }, [setSession]);

  // Re-check the Django session when the tab regains focus so an expired
  // session is eventually recognized without a full page reload.
  useEffect(() => {
    function onVisibilityChange() {
      if (document.visibilityState === "visible") {
        refreshUser();
      }
    }
    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => {
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [refreshUser]);

  return (
    <AuthContext.Provider
      value={{
        user,
        status,
        isAuthenticated: status === "authenticated",
        loginError,
        refreshUser,
        login,
        signup,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}