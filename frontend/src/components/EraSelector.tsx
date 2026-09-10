import type { Era } from "../types/discovery";

type EraSelectorProps = {
  selected: Era | null;
  onChange: (era: Era | null) => void;
};

const ERAS: { value: Era; label: string }[] = [
  { value: "1970s", label: "1970s" },
  { value: "1980s", label: "1980s" },
  { value: "1990s", label: "1990s" },
  { value: "2000s", label: "2000s" },
  { value: "2010s", label: "2010s" },
  { value: "2020s", label: "2020s" },
];

function EraSelector({ selected, onChange }: EraSelectorProps) {
  return (
    <fieldset className="selector">
      <legend className="selector__label">Era</legend>
      <div className="selector__options">
        {ERAS.map((era, index) => {
          const isSelected = selected === era.value;
          return (
            <button
              key={era.value}
              type="button"
              className={`pill pill--compact pill--era${isSelected ? " pill--selected" : ""}`}
              style={{ animationDelay: `${index * 0.45}s` }}
              aria-pressed={isSelected}
              onClick={() => onChange(isSelected ? null : era.value)}
            >
              {era.label}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}

export default EraSelector;