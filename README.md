# 🎵 HarmonIQ

**HarmonIQ** is a Django + Django REST Framework backend that layers a smart, personalized music-discovery experience on top of the Spotify Web API. It is designed as a clean, thin **API-only** service — the frontend (e.g. a React SPA) never talks to Spotify directly; every Spotify call is proxied and coordinated through HarmonIQ.

Rather than dumping raw Spotify data, HarmonIQ introduces its own domain concepts — **saved tracks**, **user preferences**, and **discovery sessions** — so the app can grow recommendation logic independently of the Spotify API shape.

---

## ✨ Features

- 🔐 **Spotify OAuth flow** — Full Authorization Code flow with automatic token storage and refresh-token support.
- 👤 **User preferences** — Store genres, eras, default mood, discovery style, and recommendation frequency per user.
- 🎧 **Saved tracks** — Persist the user's saved/favorite tracks with deduplication per user.
- 🧭 **Discovery sessions** — Model exploratory listening intent (mood, genre, era, artist, discovery style) for future recommendation engines.
- 🎛️ **Spotify proxy layer** — Server-side proxying of `/me`, `/search`, `/tracks`, `/artists`, `/albums`, `/top-tracks`, and `/top-artists`, keeping credentials and tokens off the client.
- 🧱 **Clean service-layer architecture** — `Services do the work. Views coordinate.` No Spotify URLs, headers, or HTTP details leak into views.
- 🌐 **CORS-enabled** — Ready for a separate frontend origin.
- 🗄️ **SQLite by default** with a drop-in PostgreSQL configuration via `DATABASE_URL`.

---

## 🏗️ Architecture

HarmonIQ is built around a strict separation of concerns. The canonical Spotify integration lives in `music/services/spotify.py`; the `users` app re-exports it so both apps share one implementation.

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend (React, etc.)             │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTPS / JSON (REST API)
┌──────────────────────────▼──────────────────────────────┐
│                     Django / DRF                        │
│  ┌──────────┐  ┌──────────┐  ┌─────────────────────┐   │
│  │  users   │  │  music   │  │  recommendations    │   │
│  │prefs +   │  │saved  +  │  │ discovery sessions  │   │
│  │OAuth     │  │Spotify   │  │                     │   │
│  └──────────┘  │ proxy    │  └─────────────────────┘   │
│                └────┬─────┘                            │
└────────────────┐    │    └────────────────────────────┘
                 │    │    SpotifyService (service layer)
                 ▼    ▼
         ┌──────────────────────┐
         │   Spotify Web API    │
         └──────────────────────┘
```

### Project layout

```
HarmonIQ/
├── manage.py                  # Django entry point
├── config/                    # Project settings, URLs, WSGI/ASGI
│   ├── settings.py            # App config, Spotify OAuth env, DB
│   └── urls.py                # Root URL routing
│
├── users/                     # User management + Spotify OAuth
│   ├── models.py              # UserPreference, SpotifyConnection
│   ├── services/spotify.py    # OAuth auth service (token exchange/refresh)
│   ├── views.py               # UserPreferenceView (DRF)
│   └── spotify_views.py       # spotify_login, spotify_callback
│
├── music/                     # Tracks + Spotify proxy
│   ├── models.py              # SavedTrack
│   ├── services/spotify.py    # Canonical SpotifyService client
│   ├── views.py               # SavedTrackListCreateView (DRF)
│   └── spotify_views.py       # Thin proxy: me, search, track/artist/album, top-*
│
└── recommendations/           # Future discovery engine groundwork
    ├── models.py              # DiscoverySession
    └── views.py               # DiscoverySessionListCreateView (DRF)
```

### Technical decisions

- **`music/services/spotify.py` is the canonical Spotify client.** It centralizes `requests`, auth headers, error mapping (`SpotifyAPIError`), and enforced API limits (e.g. `/search` clamped to 10, `/top-*` to 50) in one testable place.
- **`music/spotify_views.py` is a thin proxy.** It resolves a `SpotifyService` from, in priority order: (1) a `Bearer` token header, (2) the Django session, (3) the logged-in user's persisted `SpotifyConnection`. It maps Spotify errors to meaningful HTTP status codes and keeps raw Spotify details out of the core views.
- **`users/services/spotify.py` re-exports** the canonical `SpotifyService` and adds the OAuth `SpotifyAuthService` (authorization URL, token exchange, token refresh).
- **Domain models are intentionally separate from Spotify's shape** so recommendations can evolve without being coupled to Spotify's API contract.

---

## 🧩 Data Model

### `users.SpotifyConnection`
One-to-one link between a Django user and their Spotify account. Stores the Spotify account ID and OAuth tokens (**always keep `refresh_token` and `access_token` secret**).

| Field | Purpose |
|---|---|
| `user` | OneToOne → Django user |
| `spotify_account_id` | Unique Spotify user ID |
| `access_token` | Short-lived Spotify access token |
| `refresh_token` | Long-lived token to refresh access |
| `token_expires_at` | Expiry for proactive refresh |

### `users.UserPreference`
Per-user listening preferences used to drive future recommendations.

| Field | Purpose |
|---|---|
| `favorite_genres` / `preferred_eras` | JSON lists |
| `default_mood` | e.g. "chill", "energetic" |
| `discovery_style` | `familiar` / `balanced` / `new` |
| `recommendation_frequency` | `daily` / `weekly` / `on_demand` |

### `music.SavedTrack`
A track a user chose to save, with deduplication enforced by a unique constraint on `(user, spotify_track_id)`.

### `recommendations.DiscoverySession`
Captures a one-off exploratory intent (mood, genre, era, artist, discovery style) — the seed for building out recommendation algorihtms.

---

## 🔌 API Endpoints

All endpoints are under `/api/`.

### Users
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET/PATCH` | `/api/users/preferences/` | Retrieve or update the current user's preferences | Authenticated |
| `GET` | `/api/users/spotify/login/` | Redirect to Spotify authorization | — |
| `GET` | `/api/users/spotify/callback/` | OAuth callback; saves user + connection | — |

### Music (DRF + Spotify proxy)
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET/POST` | `/api/music/saved/` | List / create saved tracks | Authenticated |
| `GET` | `/api/music/me/` | Current Spotify profile | Bearer/session |
| `GET` | `/api/music/search/?q=...` | Search tracks/artists/albums | Bearer/session |
| `GET` | `/api/music/tracks/<spotify_id>/` | Track details | Bearer/session |
| `GET` | `/api/music/artists/<spotify_id>/` | Artist details | Bearer/session |
| `GET` | `/api/music/albums/<spotify_id>/` | Album details | Bearer/session |
| `GET` | `/api/music/top-tracks/` | User's top tracks | Bearer/session |
| `GET` | `/api/music/top-artists/` | User's top artists | Bearer/session |

### Recommendations
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET/POST` | `/api/recommendations/sessions/` | List / create discovery sessions | Authenticated |

**Auth header alternative:** the Spotify proxy endpoints also accept a `Authorization: Bearer <spotify_access_token>` header, which is handy for React/testing without a Django session.

---

## 🧰 Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Django 5.2 |
| API | Django REST Framework |
| HTTP | `requests` |
| Auth | Spotify OAuth 2.0 (Authorization Code + PKCE-ready) |
| Database | SQLite (dev) / PostgreSQL via `DATABASE_URL` (production) |
| Env | `python-dotenv` |
| CORS | `django-cors-headers` |
| Static files | `whitenoise` (production) |
| WSGI server | `gunicorn` (production) |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- A [Spotify Developer](https://developer.spotify.com/dashboard) app with a Client ID and Client Secret
- `pip` (venv recommended)

### 1. Clone & set up the environment

```bash
git clone https://github.com/<your-org>/HarmonIQ.git
cd HarmonIQ
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
# source venv/bin/activate

pip install -r requirements.txt
```

> If no `requirements.txt` exists yet, create it from your environment:
> ```bash
> pip freeze > requirements.txt
> ```

### 2. Configure environment variables

Copy the example file and edit it — `.env` is git-ignored:

```bash
cp .env.example .env   # Windows: copy .env.example .env
```

Every setting is read from the environment (see `.env.example` for the full
list with safe placeholders):

```env
# Django
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Frontend origins (comma-separated)
CORS_ALLOWED_ORIGINS=http://localhost:5173
CSRF_TRUSTED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
FRONTEND_URL=http://localhost:5173

# Spotify OAuth
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8000/api/users/spotify/callback/

# Database — leave empty locally to stay on SQLite
DATABASE_URL=
```

Make sure the same Redirect URI is registered in your [Spotify app dashboard](https://developer.spotify.com/dashboard).

#### Production configuration

With `DEBUG=False`, `SECRET_KEY` and `ALLOWED_HOSTS` must be set or Django
refuses to start. Set `DATABASE_URL` to a PostgreSQL URL to switch the
database backend:

```env
DEBUG=False
SECRET_KEY=<long random value>
ALLOWED_HOSTS=<cloud-run-host>
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

Collect static files before serving (WhiteNoise serves them from the app):

```bash
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

### 3. Run migrations & start the server

```bash
python manage.py migrate
python manage.py runserver
```

Your API will be available at `http://127.0.0.1:8000/api/`.

### 4. Test the Spotify integration

You can smoke-test the proxy with the included script (`test_spotify.py`), which talks to the service layer directly through Django:

```bash
python test_spotify.py
```

---

## 🧪 Testing

HarmonIQ ships with Django's test framework. Run the suite with:

```bash
python manage.py test
```

Test files live alongside each app (`users/tests.py`, `music/tests.py`, `recommendations/tests.py`) and are ready for you to extend.

---

## 🔮 Roadmap

- [ ] Access-token refresh on `401` via `SpotifyAuthService.refresh_access_token`
- [ ] Real recommendation engine based on `DiscoverySession` + `UserPreference`
- [ ] More granular Spotify permissions (playlist-modify, etc.)
- [ ] Cloud Run / Cloud SQL deployment (container build + live secrets)
- [ ] Schema/API documentation (OpenAPI/Swagger)

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

*Built with Django, DRF, and the Spotify Web API.*
