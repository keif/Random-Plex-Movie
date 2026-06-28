# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- `Dockerfile` and `docker-compose.yml` for containerised deployment
- `PLEX_URL` and `PLEX_TOKEN` environment variables — take precedence over `config.ini` (useful for Docker and CI)
- `host.docker.internal` default in `docker-compose.yml` so the container can reach a Plex server running on the host

### Changed
- Flask now binds to `0.0.0.0` so the port is reachable from outside the container
- Browser auto-open is skipped when running inside Docker

## [2.0.0] - 2026-06-28

### Added
- Movie cards now display summary, audience rating, and genres
- Loading spinner shown while fetching a random movie
- Error state displayed when Plex is unreachable or the library is empty
- "No clients online" message when no Plex clients are available
- Play failures surface in the UI instead of silently doing nothing
- 14 pytest tests covering all endpoints and error paths
- `pyproject.toml` and `uv.lock` for reproducible installs

### Changed
- Replaced Eel desktop wrapper with a Flask web server — any browser now works
- Upgraded `plexapi` from 4.5 to 4.18
- Replaced `pip` / `requirements.txt` with `uv` — run `uv sync` to install
- Launch command is now `uv run python randomPlexMovie.py`
- Dynamic DOM content built with `createElement`/`textContent` instead of `innerHTML +=`

### Fixed
- Crash when Plex returns a movie with no duration metadata
- Plex token stripped from any error messages shown in the browser
- Confusing swapped button IDs (`btn_watch` / `btn_next` now match their labels)
- Unexpected Plex API exceptions now return JSON instead of an HTML error page

### Removed
- Eel dependency and Chrome requirement
- `requirements.txt`
- `[set_path]` config section (Chrome path override no longer needed)

[Unreleased]: https://github.com/keif/Random-Plex-Movie/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/keif/Random-Plex-Movie/releases/tag/v2.0.0
