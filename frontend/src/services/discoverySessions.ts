import type { DiscoverySession } from "../types/discoverySession";
import { API_BASE_URL, apiRequest } from "./api";

const SESSIONS_URL = `${API_BASE_URL}/api/recommendations/sessions/`;

export async function getDiscoverySessions(): Promise<DiscoverySession[]> {
  return apiRequest<DiscoverySession[]>(SESSIONS_URL, "GET");
}