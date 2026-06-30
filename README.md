# Random Plex Movie

A companion web app that picks a random unwatched movie from your Plex library and sends it to any active Plex client.

It runs alongside Plex as a separate page at `http://localhost:4000` — not inside the Plex UI. Hit **NEXT** to pick a random movie, then **WATCH** to start playback on any connected client (Apple TV, Plex app on your TV, etc.).

[![GitHub Release](https://img.shields.io/github/v/release/Akasiek/Random-Plex-Movie?include_prereleases&label=Release&style=flat-square)](https://github.com/Akasiek/Random-Plex-Movie/releases)
[![GitHub](https://img.shields.io/github/license/Akasiek/random-plex-movie?style=flat-square)](https://github.com/Akasiek/random-plex-movie/blob/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/PlexAPI?label=PlexAPI&style=flat-square)](https://pypi.org/project/PlexAPI/)
[![Docker Hub](https://img.shields.io/docker/v/ikeif/random-plex-movie?label=Docker%20Hub&style=flat-square)](https://hub.docker.com/r/ikeif/random-plex-movie)

![Example selection screenshot](/screenshot.png)
![Example agent selection screenshot](/agents.png)

## Running with Docker

The quickest way to get started. Requires [Docker](https://docs.docker.com/get-docker/).

1. Clone the repo:

```bash
git clone https://github.com/Akasiek/Random-Plex-Movie.git
cd Random-Plex-Movie
```

2. Create a `.env` file from the example and add your Plex token:

```bash
cp .env.example .env
```

```ini
PLEX_TOKEN=your-token-here
```

To find your token, see: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/

`.env` is gitignored — your token will never be accidentally committed.

3. Start the container:

```bash
docker compose up -d
```

The image is published on Docker Hub as [`ikeif/random-plex-movie`](https://hub.docker.com/r/ikeif/random-plex-movie). `docker-compose.yml` pulls it automatically — no local build required.

Open `http://localhost:4000` in your browser.

> **Linux users:** Uncomment the `extra_hosts` block in `docker-compose.yml` — Docker Desktop on macOS handles `host.docker.internal` automatically, but Linux needs it explicitly.

> **Plex in Docker:** If your Plex server is also a Docker container, replace `host.docker.internal:32400` with your Plex container's service name, e.g. `http://plex:32400`, and add both services to the same Docker network.

---

## Running without Docker

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

1. Clone the repo:

```bash
git clone https://github.com/Akasiek/Random-Plex-Movie.git
cd Random-Plex-Movie
```

2. Install dependencies:

```bash
uv sync
```

3. Edit `config/config.ini` with your Plex credentials:

```ini
[auth]
baseurl = http://localhost:32400
token = your-token-here
```

4. Run:

```bash
uv run python randomPlexMovie.py
```

The app starts on port 4000 and opens your default browser automatically. Press **NEXT** to pick a new random movie, or **WATCH** to send the current movie to a connected Plex client.

## Configuration

Settings are read from `config/config.ini`. Environment variables take precedence and are the recommended approach for Docker:

| Env var | config.ini equivalent | Default |
|---|---|---|
| `PLEX_URL` | `[auth] baseurl` | `http://localhost:32400` |
| `PLEX_TOKEN` | `[auth] token` | _(none)_ |
| `PLEX_LIBRARY` | `[auth] library` | `Movies` |

## Development

Run the test suite:

```bash
uv run pytest
```
