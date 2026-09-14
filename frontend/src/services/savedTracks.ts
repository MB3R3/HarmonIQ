import type { SaveTrackPayload, SavedTrack } from "../types/savedTrack";
import {
  API_BASE_URL,
  fetchCsrfToken,
  isCsrfFailure,
  resetCsrfToken,
  translateApiError,
} from "./api";

const SAVED_TRACKS_URL = `${API_BASE_URL}/api/music/saved/`;

async function request<T>(
  url: string,
  method: string,
  body?: unknown
): Promise<T> {
  let csrfToken = await fetchCsrfToken();

  for (let attempt = 0; attempt < 2; attempt += 1) {
    let response: Response;
    try {
      const init: RequestInit = {
        method,
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        credentials: "include",
      };
      if (body !== undefined) {
        init.body = JSON.stringify(body);
      }
      response = await fetch(url, init);
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
      throw new Error(
        translateApiError(
          response.status,
          data,
          "Unable to complete this request. Please try again."
        )
      );
    }

    return data as T;
  }

  throw new Error(
    "Unable to complete this request. Please try again."
  );
}

export async function getSavedTracks(): Promise<SavedTrack[]> {
  return request<SavedTrack[]>(SAVED_TRACKS_URL, "GET");
}

export async function saveTrack(
  payload: SaveTrackPayload
): Promise<SavedTrack> {
  return request<SavedTrack>(SAVED_TRACKS_URL, "POST", payload);
}

export async function deleteSavedTrack(id: number): Promise<void> {
  const url = `${SAVED_TRACKS_URL}${id}/`;
  await request<null>(url, "DELETE");
}