import type { DiscoveryForm } from "../types/discovery";
import type {
  DiscoveryRequestPayload,
  DiscoveryResponse,
} from "../types/recommendation";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000"
).replace(/\/$/, "");

const CSRF_URL = `${API_BASE_URL}/api/users/csrf/`;
const DISCOVER_URL = `${API_BASE_URL}/api/recommendations/discover/`;

let csrfTokenPromise: Promise<string> | null = null;

function getCookie(name: string): string | null {
  const match = document.cookie.match(
    new RegExp(`(?:^|; )${name}=([^;]*)`)
  );
  return match ? decodeURIComponent(match[1]) : null;
}

async function fetchCsrfToken(): Promise<string> {
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

function buildPayload(form: DiscoveryForm): DiscoveryRequestPayload {
  return {
    mood: form.mood ?? "",
    genre: form.genre ?? "",
    era: form.era ?? "",
    artist: form.artist.trim(),
    discovery_style: form.discoveryStyle,
  };
}

function isCsrfFailure(status: number, data: unknown): boolean {
  if (status !== 403) return false;
  if (data && typeof data === "object") {
    const detail = (data as { detail?: unknown }).detail;
    return typeof detail === "string" && detail.includes("CSRF");
  }
  return false;
}

function translateApiError(status: number, data: unknown): string {
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

  if (data && typeof data === "object") {
    const error = (data as { error?: unknown }).error;
    if (typeof error === "string") {
      const message = error.toLowerCase();
      if (message.includes("spotify") && message.includes("connect")) {
        return (
          "Make sure your Spotify account is connected, then try again."
        );
      }
      if (message.includes("spotify")) {
        return "Spotify is having trouble right now. Please try again.";
      }
    }
  }

  return "Unable to discover music right now. Please try again.";
}

export async function discoverMusic(
  form: DiscoveryForm
): Promise<DiscoveryResponse> {
  let csrfToken = await fetchCsrfToken();

  for (let attempt = 0; attempt < 2; attempt += 1) {
    let response: Response;
    try {
      response = await fetch(DISCOVER_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        credentials: "include",
        body: JSON.stringify(buildPayload(form)),
      });
    } catch {
      throw new Error(
        "Unable to reach HarmonIQ. Make sure the server is running " +
          `at ${API_BASE_URL}.`
      );
    }

    let data: unknown;
    try {
      data = await response.json();
    } catch {
      data = null;
    }

    if (!response.ok) {
      if (isCsrfFailure(response.status, data) && attempt === 0) {
        csrfTokenPromise = null;
        csrfToken = await fetchCsrfToken();
        continue;
      }
      throw new Error(translateApiError(response.status, data));
    }

    return data as DiscoveryResponse;
  }

  throw new Error("Unable to discover music right now. Please try again.");
}