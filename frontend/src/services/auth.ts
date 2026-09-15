import type { SessionStatus, SignupPayload } from "../types/auth";
import {
  API_BASE_URL,
  apiRequest,
  isCsrfFailure,
  resetCsrfToken,
} from "./api";

const CURRENT_USER_URL = `${API_BASE_URL}/api/users/me/`;
const LOGIN_URL = `${API_BASE_URL}/api/users/login/`;
const LOGOUT_URL = `${API_BASE_URL}/api/users/logout/`;
const SIGNUP_URL = `${API_BASE_URL}/api/users/signup/`;

export async function getCurrentUser(): Promise<SessionStatus> {
  return apiRequest<SessionStatus>(CURRENT_USER_URL, "GET");
}

export async function signupUser(
  payload: SignupPayload
): Promise<SessionStatus> {
  const session = await apiRequest<SessionStatus>(
    SIGNUP_URL,
    "POST",
    payload,
    translateAuthError
  );
  resetCsrfToken();
  return session;
}

export async function loginUser(
  username: string,
  password: string
): Promise<SessionStatus> {
  const session = await apiRequest<SessionStatus>(
    LOGIN_URL,
    "POST",
    { username, password },
    translateAuthError
  );
  resetCsrfToken();
  return session;
}

export async function logoutUser(): Promise<void> {
  await apiRequest<null>(LOGOUT_URL, "POST");
}

function translateAuthError(
  status: number,
  data: unknown,
  fallback: string
): string {
  if (data && typeof data === "object" && "error" in data) {
    return String((data as { error: unknown }).error);
  }
  if (isCsrfFailure(status, data)) {
    return (
      "A security check failed (cookies). Refresh the page and try again — " +
      "your browser must accept cookies for the API server."
    );
  }
  return fallback;
}