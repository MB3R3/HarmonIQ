export type Mood =
  | "chill"
  | "energetic"
  | "melancholic"
  | "happy"
  | "focus"
  | "romantic";

export type Genre =
  | "r&b"
  | "hip-hop"
  | "pop"
  | "rock"
  | "jazz"
  | "afrobeats";

export type Era =
  | "1970s"
  | "1980s"
  | "1990s"
  | "2000s"
  | "2010s"
  | "2020s";

export type DiscoveryStyle = "familiar" | "balanced" | "new";

export type DiscoveryForm = {
  mood: Mood | null;
  genre: Genre | null;
  era: Era | null;
  artist: string;
  discoveryStyle: DiscoveryStyle;
};