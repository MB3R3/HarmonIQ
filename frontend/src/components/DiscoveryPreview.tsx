type PreviewField = {
  label: string;
  value: string;
};

const MODIFIER_FIELDS: PreviewField[] = [
  { label: "Mood", value: "Chill" },
  { label: "Genre", value: "R&B" },
  { label: "Era", value: "2010s" },
  { label: "Artist", value: "Frank Ocean" },
];

const STYLE_OPTIONS = ["Familiar", "Balanced", "New"];

function DiscoveryPreview() {
  return (
    <section id="discovery" className="preview section">
      <div className="container">
        <div className="preview__heading">
          <p className="eyebrow">The discovery builder</p>
          <h2>Tell HarmonIQ what you want to hear.</h2>
        </div>

        <div className="preview__grid">
          <div className="preview__controls">
            {MODIFIER_FIELDS.map((field) => (
              <div className="preview__row" key={field.label}>
                <span className="preview__label">{field.label}</span>
                <button
                  type="button"
                  className="pill pill--selected"
                  aria-pressed="true"
                >
                  {field.value}
                </button>
              </div>
            ))}

            <div className="preview__row">
              <span className="preview__label">Discovery style</span>
              <div className="preview__pill-group">
                {STYLE_OPTIONS.map((option) => (
                  <button
                    key={option}
                    type="button"
                    className={`pill${option === "Balanced" ? " pill--selected" : ""}`}
                    aria-pressed={option === "Balanced"}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <aside className="preview__result" aria-label="Example result">
            <span className="preview__result-label">
              Your discovery mix
            </span>
            <div className="preview__result-title">
              Chill R&amp;B for late nights
            </div>
            <p className="preview__result-copy">
              Built from your direction, refined by your taste.
            </p>
            <div className="preview__result-foot">
              <span className="preview__result-count">10 tracks</span>
              <span className="preview__result-score">Score 60</span>
            </div>
          </aside>
        </div>
      </div>
    </section>
  );
}

export default DiscoveryPreview;