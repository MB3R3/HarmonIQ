type ArtistInputProps = {
  value: string;
  onChange: (value: string) => void;
};

function ArtistInput({ value, onChange }: ArtistInputProps) {
  return (
    <div className="selector">
      <label className="selector__label" htmlFor="artist-input">
        Artist
      </label>
      <input
        id="artist-input"
        type="text"
        className="input"
        placeholder="Search by artist (optional)"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}

export default ArtistInput;