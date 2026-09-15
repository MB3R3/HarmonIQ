export type AuthStatus =
  | "loading"
  | "authenticated"
  | "unauthenticated";

export type AuthUser = {
  id: number;
  username: string;
  email: string;
  spotify_connected: boolean;
  spotify_display_name: string | null;
};

export type SessionStatus = {
  authenticated: boolean;
  user: AuthUser | null;
};

export type SignupPayload = {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
};