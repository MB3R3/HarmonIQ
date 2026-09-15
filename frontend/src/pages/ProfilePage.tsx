import { useState } from "react";

import { API_BASE_URL } from "../services/api";
import { useAuth } from "../context/useAuth";

const SPOTIFY_LOGIN_URL = `${API_BASE_URL}/api/users/spotify/login/`;

function ProfilePage() {
  const { user, logout } = useAuth();
  const [isSigningOut, setIsSigningOut] = useState(false);

  const handleSignOut = async () => {
    setIsSigningOut(true);
    try {
      await logout();
    } finally {
      setIsSigningOut(false);
    }
  };

  if (!user) {
    return null;
  }

  return (
    <section className="profile">
      <header className="profile__header">
        <h1 className="profile__title">Profile</h1>
        <p className="profile__subtitle">
          Your HarmonIQ account and music connections.
        </p>
      </header>

      <div className="profile__grid">
        <div className="profile-card">
          <h2 className="profile-card__title">HarmonIQ</h2>

          <dl className="profile-fields">
            <div className="profile-field">
              <dt className="profile-field__label">Username</dt>
              <dd className="profile-field__value">
                <span className="profile-field__handle">
                  @{user.username}
                </span>
              </dd>
            </div>
            <div className="profile-field">
              <dt className="profile-field__label">Email</dt>
              <dd className="profile-field__value">{user.email}</dd>
            </div>
          </dl>
        </div>

        <div className="profile-card">
          <h2 className="profile-card__title">Spotify</h2>

          <div className="profile-field">
            <span className="profile-field__label">Connection</span>
            <span
              className={`profile-status${
                user.spotify_connected
                  ? " profile-status--connected"
                  : " profile-status--disconnected"
              }`}
            >
              <span className="profile-status__dot" aria-hidden="true" />
              {user.spotify_connected ? "Connected" : "Not connected"}
            </span>
          </div>

          <p className="profile-card__copy">
            {user.spotify_connected && user.spotify_display_name ? (
              <>
                Connected as <strong>{user.spotify_display_name}</strong>.
                Your HarmonIQ username stays @{user.username}.
              </>
            ) : user.spotify_connected ? (
              "Your Spotify account is linked. Reconnect any time to refresh your profile."
            ) : (
              "Connect Spotify to personalize your music discovery."
            )}
          </p>

          {user.spotify_connected ? (
            <span
              className="button button--secondary profile-card__action profile-card__badge"
              aria-hidden="true"
            >
              Spotify Connected
            </span>
          ) : (
            <a
              href={SPOTIFY_LOGIN_URL}
              className="button button--secondary profile-card__action"
            >
              Connect Spotify
            </a>
          )}
        </div>

        <div className="profile-card">
          <h2 className="profile-card__title">Session</h2>
          <p className="profile-card__copy">
            Signed in as {user.username}. Sign out to end this session on
            this device.
          </p>
          <button
            type="button"
            className="button button--secondary profile-card__action profile-card__action--danger"
            onClick={handleSignOut}
            disabled={isSigningOut}
          >
            {isSigningOut ? "Signing out…" : "Sign out"}
          </button>
        </div>
      </div>
    </section>
  );
}

export default ProfilePage;