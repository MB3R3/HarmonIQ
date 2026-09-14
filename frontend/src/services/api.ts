export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000"
).replace(/\/$/, "");

const CSRF_URL = `${API_BASE_URL}/api/users/csrf/`;

let csrfTokenPromise: Promise<string> | null = null;

export function getCookie(name: string): string | null {
  const match = document.cookie.match(
    new RegExp(`(?:^|; )${name}=([^;]*)`)
  );
  return match ? decodeURIComponent(match[1]) : null;
}

export function resetCsrfToken(): void {
  csrfTokenPromise = null;
}

export async function fetchCsrfToken(): Promise<string> {
  if (!csrfTokenPromise) {
    csrfTokenPromise = fetch(CSRF_URL, {
      method: "GET",
      credentials: "include",
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`CSRF endpoint returned ${response.status}`);
        }
        const data = (await response.json()) as { csrfToken?: string };
        return data.csrfToken ?? getCookie("csrftoken") ?? "";
      })
      .catch((error: unknown) => {
        csrfTokenPromise = null;
        throw error;
      });
  }
  return csrfTokenPromise;
}

export function isCsrfFailure(status: number, data: unknown): boolean {
  if (status !== 403) return false;
  if (data && typeof data === "object") {
    const detail = (data as { detail?: unknown }).detail;
    return typeof detail === "string" && detail.includes("CSRF");
  }
  return false;
}

export function translateApiError(
  status: number,
  data: unknown,
  fallback: string
): string {
  if (isCsrfFailure(status, data)) {
    return (
      "A security check failed (cookies). Refresh the page and try again — " +
      "your browser must accept cookies for the API server."
    );
  }

  if (status === 401 || status === 403) {
    return (
      "You need to sign in to use HarmonIQ. Log in on the server, " +
      "then try again."
    );
  }

  return fallback;
}