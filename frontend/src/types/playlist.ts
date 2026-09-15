export interface CreatePlaylistPayload {
  name: string;
  description: string;
  public: boolean;
  track_ids: string[];
}

export interface CreatedPlaylist {
  id: string;
  name: string;
  spotify_url: string;
  public: boolean;
  track_count: number;
}

export interface CreatePlaylistResponse {
  playlist: CreatedPlaylist;
}