import type {
  DiscoveryStyle,
  Era,
  Genre,
  Mood,
} from "../types/discovery";

export const MOOD_OPTIONS: { value: Mood; label: string }[] = [
  { value: "chill", label: "Chill" },
  { value: "energetic", label: "Energetic" },
  { value: "melancholic", label: "Melancholic" },
  { value: "happy", label: "Happy" },
  { value: "focus", label: "Focus" },
  { value: "romantic", label: "Romantic" },
];

export const GENRE_OPTIONS: { value: Genre; label: string }[] = [
  { value: "r&b", label: "R&B" },
  { value: "hip-hop", label: "Hip-Hop" },
  { value: "pop", label: "Pop" },
  { value: "rock", label: "Rock" },
  { value: "jazz", label: "Jazz" },
  { value: "afrobeats", label: "Afrobeats" },
];

export const ERA_OPTIONS: { value: Era; label: string }[] = [
  { value: "1970s", label: "1970s" },
  { value: "1980s", label: "1980s" },
  { value: "1990s", label: "1990s" },
  { value: "2000s", label: "2000s" },
  { value: "2010s", label: "2010s" },
  { value: "2020s", label: "2020s" },
];

export const STYLE_OPTIONS: {
  value: DiscoveryStyle;
  label: string;
  hint: string;
}[] = [
  {
    value: "familiar",
    label: "Familiar",
    hint: "More music similar to what you already know.",
  },
  {
    value: "balanced",
    label: "Balanced",
    hint: "A mix of familiar and new.",
  },
  {
    value: "new",
    label: "New",
    hint: "Push further outside your usual listening.",
  },
];

export const STYLE_LABELS: Record<DiscoveryStyle, string> = {
  familiar: "Familiar",
  balanced: "Balanced",
  new: "New",
};