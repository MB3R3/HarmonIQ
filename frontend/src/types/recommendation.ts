import type { DiscoveryStyle } from "./discovery";

export interface Recommendation {
  spotify_track_id: string;
  name: string;
  artist: string;
  album: string;
  artwork_url: string;
  spotify_url: string;
  score: number;
  reasons: string[];
}

export interface DiscoveryRequestPayload {
  mood: string;
  genre: string;
  era: string;
  artist: string;
  discovery_style: DiscoveryStyle;
}

export interface DiscoveryResponse {
  request: DiscoveryRequestPayload;
  results: Recommendation[];
}