import ArtistInput from "./ArtistInput";
import DiscoveryStyleSelector from "./DiscoveryStyleSelector";
import EraSelector from "./EraSelector";
import GenreSelector from "./GenreSelector";
import MoodSelector from "./MoodSelector";
import type { DiscoveryForm } from "../types/discovery";

type DiscoveryBuilderProps = {
  form: DiscoveryForm;
  onChange: (form: DiscoveryForm) => void;
  onSubmit: (form: DiscoveryForm) => void;
};

function DiscoveryBuilder({ form, onChange, onSubmit }: DiscoveryBuilderProps) {
  return (
    <section className="builder" aria-label="Discovery builder">
      <div className="builder__grid">
        <MoodSelector
          selected={form.mood}
          onChange={(mood) => onChange({ ...form, mood })}
        />
        <GenreSelector
          selected={form.genre}
          onChange={(genre) => onChange({ ...form, genre })}
        />
        <EraSelector
          selected={form.era}
          onChange={(era) => onChange({ ...form, era })}
        />
        <ArtistInput
          value={form.artist}
          onChange={(artist) => onChange({ ...form, artist })}
        />
      </div>

      <div className="builder__style">
        <DiscoveryStyleSelector
          selected={form.discoveryStyle}
          onChange={(discoveryStyle) => onChange({ ...form, discoveryStyle })}
        />
      </div>

      <button
        type="button"
        className="button button--primary button--large builder__cta"
        onClick={() => onSubmit(form)}
      >
        Discover Music
      </button>
    </section>
  );
}

export default DiscoveryBuilder;