const WAVE_BARS = Array.from({ length: 9 }, (_, index) => index);

function Hero() {
  return (
    <section className="hero">
      <div className="hero__inner container">
        <div className="hero__content">
          <p className="eyebrow">Music discovery, your way</p>
          <h1 className="hero__headline">
            Discover music on your terms.
          </h1>
          <p className="hero__support">
            Tell HarmonIQ what you want to hear. Choose a mood, genre,
            era, or artist and discover music that fits your direction.
          </p>
          <div className="hero__actions">
            <button type="button" className="button button--primary">
              Start Discovering
            </button>
            <button type="button" className="button button--secondary">
              Connect Spotify
            </button>
          </div>
        </div>

        <div
          className="hero__visual"
          role="img"
          aria-label="Animated speaker responding to a heartbeat-rate sound display"
        >
          <span className="hero__ring" />
          <span className="hero__ring hero__ring--delay" />
          <div className="hero__disc hero__disc--large" />
          <div className="hero__disc hero__disc--medium" />
          <span className="hero__disc hero__disc--small" />
          <div className="sound-wave">
            {WAVE_BARS.map((bar) => (
              <span
                className="sound-wave__bar"
                key={bar}
                style={{ animationDelay: `${bar * 0.13}s` }}
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

export default Hero;