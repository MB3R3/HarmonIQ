export interface SavedTrack {
  id: number;
  spotify_track_id: string;
  track_name: string;
  artist_name: string;
  album_name: string;
  artwork_url: string;
  spotify_url: string;
  saved_at: string;
}

export interface SaveTrackPayload {
  spotify_track_id: string;
  track_name: string;
  artist_name: string;
  album_name: string;
  artwork_url: string;
}