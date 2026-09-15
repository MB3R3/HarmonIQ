import { useAuth } from "../context/useAuth";
import { API_BASE_URL } from "../services/api";

const SPOTIFY_LOGIN_URL = `${API_BASE_URL}/api/users/spotify/login/`;

function Navbar() {
  const { status, user } = useAuth();

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

        {status === "unauthenticated" ? (
          <a href="#/login" className="button button--primary navbar__cta">
            Log in
          </a>
        ) : user && !user.spotify_connected ? (
          <a
            href={SPOTIFY_LOGIN_URL}
            className="button button--primary navbar__cta"
          >
            Connect Spotify
          </a>
        ) : (
          <a href="#/discover" className="button button--primary navbar__cta">
            Discover
          </a>
        )}
      </div>
    </nav>
  );
}

export default Navbar;