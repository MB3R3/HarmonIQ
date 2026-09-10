import type { DiscoveryStyle } from "../types/discovery";
import { STYLE_OPTIONS } from "../lib/discoveryOptions";

type DiscoveryStyleSelectorProps = {
  selected: DiscoveryStyle;
  onChange: (style: DiscoveryStyle) => void;
};

function DiscoveryStyleSelector({
  selected,
  onChange,
}: DiscoveryStyleSelectorProps) {
  return (
    <fieldset className="selector">
      <legend className="selector__label">Discovery style</legend>
      <div className="style-selector">
        {STYLE_OPTIONS.map((option) => {
          const isSelected = selected === option.value;
          return (
            <button
              key={option.value}
              type="button"
              className={`style-option${isSelected ? " style-option--selected" : ""}`}
              aria-pressed={isSelected}
              onClick={() => onChange(option.value)}
            >
              <span className="style-option__label">{option.label}</span>
              <span className="style-option__hint">{option.hint}</span>
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}

export default DiscoveryStyleSelector;