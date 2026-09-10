import { useState } from "react";

import ArtistInput from "./ArtistInput";
import DiscoveryStyleSelector from "./DiscoveryStyleSelector";
import EraSelector from "./EraSelector";
import GenreSelector from "./GenreSelector";
import MoodSelector from "./MoodSelector";
import type {
  DiscoveryStyle,
  Era,
  Genre,
  Mood,
} from "../types/discovery";

function DiscoveryBuilder() {
  const [mood, setMood] = useState<Mood | null>(null);
  const [genre, setGenre] = useState<Genre | null>(null);
  const [era, setEra] = useState<Era | null>(null);
  const [artist, setArtist] = useState("");
  const [discoveryStyle, setDiscoveryStyle] =
    useState<DiscoveryStyle>("balanced");

  return (
    <section className="builder" aria-label="Discovery builder">
      <div className="builder__grid">
        <MoodSelector selected={mood} onChange={setMood} />
        <GenreSelector selected={genre} onChange={setGenre} />
        <EraSelector selected={era} onChange={setEra} />
        <ArtistInput value={artist} onChange={setArtist} />
      </div>

      <div className="builder__style">
        <DiscoveryStyleSelector
          selected={discoveryStyle}
          onChange={setDiscoveryStyle}
        />
      </div>

      <button
        type="button"
        className="button button--primary button--large builder__cta"
      >
        Discover Music
      </button>
    </section>
  );
}

export default DiscoveryBuilder;