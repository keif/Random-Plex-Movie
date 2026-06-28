# Random Plex Movie

Python app that picks a random unwatched movie from your Plex library and lets you send it to any active Plex client.

[![GitHub Release](https://img.shields.io/github/v/release/Akasiek/Random-Plex-Movie?include_prereleases&label=Release&style=flat-square)](https://github.com/Akasiek/Random-Plex-Movie/releases)
[![GitHub](https://img.shields.io/github/license/Akasiek/random-plex-movie?style=flat-square)](https://github.com/Akasiek/random-plex-movie/blob/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/PlexAPI?label=PlexAPI&style=flat-square)](https://pypi.org/project/PlexAPI/)

![Example screenshot](https://i.imgur.com/CKplHDk.jpg)

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- A running Plex Media Server

## Installation

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

To find your token, see: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/

## Usage

```bash
uv run python randomPlexMovie.py
```

The app starts a local web server on port 4000 and opens your default browser automatically. Press **NEXT** to pick a new random movie, or **WATCH** to send the current movie to a connected Plex client.

## Development

Run the test suite:

```bash
uv run pytest
```
