import type { SaveTrackPayload, SavedTrack } from "../types/savedTrack";
import { API_BASE_URL, apiRequest } from "./api";

const SAVED_TRACKS_URL = `${API_BASE_URL}/api/music/saved/`;

export async function getSavedTracks(): Promise<SavedTrack[]> {
  return apiRequest<SavedTrack[]>(SAVED_TRACKS_URL, "GET");
}

export async function saveTrack(
  payload: SaveTrackPayload
): Promise<SavedTrack> {
  return apiRequest<SavedTrack>(SAVED_TRACKS_URL, "POST", payload);
}

export async function deleteSavedTrack(id: number): Promise<void> {
  await apiRequest<null>(`${SAVED_TRACKS_URL}${id}/`, "DELETE");
}