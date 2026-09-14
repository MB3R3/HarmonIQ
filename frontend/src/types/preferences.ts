export type UserPreferences = {
  favorite_genres: string[];
  preferred_eras: string[];
  default_mood: string;
  discovery_style: string;
  recommendation_frequency: string;
};

export type PreferencesUpdate = UserPreferences;