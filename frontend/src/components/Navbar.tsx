function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar__inner container">
        <a href="/" className="navbar__brand">
          HarmonIQ
        </a>

        <ul className="navbar__links">
          <li>
            <a href="#how-it-works">How it works</a>
          </li>
          <li>
            <a href="#discovery">Discovery</a>
          </li>
        </ul>

        <button type="button" className="button button--primary navbar__cta">
          Connect Spotify
        </button>
      </div>
    </nav>
  );
}

export default Navbar;