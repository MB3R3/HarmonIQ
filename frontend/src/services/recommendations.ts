import type { DiscoveryForm } from "../types/discovery";
import type {
  DiscoveryRequestPayload,
  DiscoveryResponse,
} from "../types/recommendation";
import {
  API_BASE_URL,
  fetchCsrfToken,
  isCsrfFailure,
  resetCsrfToken,
} from "./api";

const DISCOVER_URL = `${API_BASE_URL}/api/recommendations/discover/`;

function buildPayload(form: DiscoveryForm): DiscoveryRequestPayload {
  return {
    mood: form.mood ?? "",
    genre: form.genre ?? "",
    era: form.era ?? "",
    artist: form.artist.trim(),
    discovery_style: form.discoveryStyle,
  };
}

function translateDiscoverError(status: number, data: unknown): string {
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
        resetCsrfToken();
        csrfToken = await fetchCsrfToken();
        continue;
      }
      throw new Error(translateDiscoverError(response.status, data));
    }

    return data as DiscoveryResponse;
  }

  throw new Error("Unable to discover music right now. Please try again.");
}