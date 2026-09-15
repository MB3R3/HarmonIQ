import type {
  PreferencesUpdate,
  UserPreferences,
} from "../types/preferences";
import { API_BASE_URL, apiRequest } from "./api";

const PREFERENCES_URL = `${API_BASE_URL}/api/users/preferences/`;

export async function getPreferences(): Promise<UserPreferences> {
  return apiRequest<UserPreferences>(PREFERENCES_URL, "GET");
}

export async function updatePreferences(
  preferences: PreferencesUpdate
): Promise<UserPreferences> {
  return apiRequest<UserPreferences>(
    PREFERENCES_URL,
    "PUT",
    preferences
  );
}

export async function clearPreferences(): Promise<UserPreferences> {
  // Resets saved discovery defaults. The account, Spotify connection and
  // saved tracks are unaffected.
  return apiRequest<UserPreferences>(PREFERENCES_URL, "DELETE");
}