// TEMPORARY UI mock data.
// Replace with data from the Django API (e.g. saved tracks /
// recommendation results) once the API integration phase lands.

type MockTrack = {
  id: string;
  title: string;
  artist: string;
  album: string;
  artwork: string;
};

const MOCK_TRACKS: MockTrack[] = [
  {
    id: "1",
    title: "Nights",
    artist: "Frank Ocean",
    album: "Blonde",
    artwork: "linear-gradient(135deg, #2f2f3a 0%, #4a3f52 100%)",
  },
  {
    id: "2",
    title: "Self Control",
    artist: "Frank Ocean",
    album: "Blonde",
    artwork: "linear-gradient(135deg, #26272e 0%, #5a4a5e 100%)",
  },
  {
    id: "3",
    title: "Broken Clocks",
    artist: "SZA",
    album: "Ctrl",
    artwork: "linear-gradient(135deg, #332a22 0%, #6b5640 100%)",
  },
  {
    id: "4",
    title: "Pink + White",
    artist: "Frank Ocean",
    album: "Blonde",
    artwork: "linear-gradient(135deg, #282b3a 0%, #5b4b6b 100%)",
  },
  {
    id: "5",
    title: "The Weekend",
    artist: "SZA",
    album: "Ctrl",
    artwork: "linear-gradient(135deg, #232a2c 0%, #3e5560 100%)",
  },
];

function RecentDiscoveries() {
  return (
    <section className="recent" aria-label="Recent discoveries">
      <div className="recent__heading">
        <h2 className="recent__title">Recent discoveries</h2>
        <p className="recent__note">Sample data — API coming soon.</p>
      </div>

      <ul className="recent__grid">
        {MOCK_TRACKS.map((track) => (
          <li className="track" key={track.id}>
            <div
              className="track__artwork"
              style={{ background: track.artwork }}
              aria-hidden="true"
            />
            <div className="track__title">{track.title}</div>
            <div className="track__artist">{track.artist}</div>
            <div className="track__album">{track.album}</div>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default RecentDiscoveries;