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

        <div className="hero__visual" aria-hidden="true">
          <div className="hero__disc hero__disc--large" />
          <div className="hero__disc hero__disc--medium" />
          <div className="hero__disc hero__disc--small" />
        </div>
      </div>
    </section>
  );
}

export default Hero;