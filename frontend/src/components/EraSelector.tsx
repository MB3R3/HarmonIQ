import type { Era } from "../types/discovery";
import { ERA_OPTIONS } from "../lib/discoveryOptions";

type EraSelectorProps = {
  selected: Era | null;
  onChange: (era: Era | null) => void;
};

function EraSelector({ selected, onChange }: EraSelectorProps) {
  return (
    <fieldset className="selector">
      <legend className="selector__label">Era</legend>
      <div className="selector__options">
        {ERA_OPTIONS.map((era, index) => {
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