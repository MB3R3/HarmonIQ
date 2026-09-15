import type {
  CreatePlaylistPayload,
  CreatePlaylistResponse,
  CreatedPlaylist,
} from "../types/playlist";
import {
  API_BASE_URL,
  apiRequest,
  isCsrfFailure,
} from "./api";

const CREATE_PLAYLIST_URL = `${API_BASE_URL}/api/music/playlists/create/`;

function translateCreatePlaylistError(
  status: number,
  data: unknown
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

  if (data && typeof data === "object") {
    const record = data as Record<string, unknown>;
    if (typeof record.error === "string" && record.error) {
      return record.error;
    }
    if (typeof record.detail === "string" && record.detail) {
      return record.detail;
    }
    const fieldMessage = Object.values(record)
      .filter((value): value is unknown[] => Array.isArray(value))
      .map((messages) =>
        messages.find((message) => typeof message === "string")
      )
      .find((message): message is string => typeof message === "string");
    if (fieldMessage) {
      return fieldMessage;
    }
  }

  return "Unable to create your playlist. Please try again.";
}

export async function createSpotifyPlaylist(
  payload: CreatePlaylistPayload
): Promise<CreatedPlaylist> {
  const response = await apiRequest<CreatePlaylistResponse>(
    CREATE_PLAYLIST_URL,
    "POST",
    payload,
    translateCreatePlaylistError
  );
  return response.playlist;
}