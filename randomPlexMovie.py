import configparser
import os
import re
import threading
import webbrowser
from random import choice
from urllib.request import Request, urlopen

from flask import Flask, Response, jsonify, request, send_from_directory
from plexapi.server import PlexServer

app = Flask(__name__, static_folder="web", static_url_path="")

_config = configparser.ConfigParser()
_config.read("config/config.ini")

# Env vars take precedence over config.ini (useful for Docker)
_plex_url = os.environ.get("PLEX_URL") or _config.get("auth", "baseurl", fallback="http://localhost:32400")
_plex_token = os.environ.get("PLEX_TOKEN") or _config.get("auth", "token", fallback="")
_plex_library = os.environ.get("PLEX_LIBRARY") or _config.get("auth", "library", fallback="Movies")

_plex = None
_movies = None
_plex_error = None
_chosen_movie = None


def _in_docker():
    return os.path.exists("/.dockerenv")


def _scrub_token(text):
    return re.sub(r"X-Plex-Token=[^&\s\"']+", "X-Plex-Token=REDACTED", str(text))


def _connect_plex():
    global _plex, _movies, _plex_error
    try:
        _plex = PlexServer(_plex_url, _plex_token)
        _movies = _plex.library.section(_plex_library)
    except Exception as exc:
        _plex_error = _scrub_token(exc)


@app.route("/")
def index():
    return send_from_directory("web", "index.html")


_PLEX_IMAGE_RE = re.compile(r"^/library/(metadata|parts)/\d+/(thumb|art)/\d+$")


@app.route("/api/image")
def proxy_image():
    path = request.args.get("path", "")
    if not _PLEX_IMAGE_RE.match(path):
        return "", 400
    try:
        req = Request(f"{_plex_url}{path}", headers={"X-Plex-Token": _plex_token})
        with urlopen(req, timeout=10) as r:
            return Response(r.read(), content_type=r.headers.get("Content-Type", "image/jpeg"))
    except Exception:
        app.logger.exception("proxy_image failed")
        return "", 502


@app.route("/api/status")
def get_status():
    if _plex_error:
        return jsonify({"ok": False, "error": _plex_error})
    try:
        _plex.query("/")
        return jsonify({"ok": True})
    except Exception:
        return jsonify({"ok": False, "error": "Plex is unreachable"})


@app.route("/api/movie")
def get_movie():
    if _plex_error:
        return jsonify({"error": _plex_error}), 503
    global _chosen_movie
    try:
        unwatched = _movies.search(unwatched=True)
        if not unwatched:
            return jsonify({"error": "No unwatched movies in your library"}), 404
        _chosen_movie = choice(unwatched)
        hours = int((_chosen_movie.duration / (1000 * 60 * 60)) % 24) if _chosen_movie.duration else 0
        minutes = int((_chosen_movie.duration / (1000 * 60)) % 60) if _chosen_movie.duration else 0
        return jsonify({
            "title": _chosen_movie.title,
            "year": _chosen_movie.year,
            "duration_hours": hours,
            "duration_minutes": minutes,
            "summary": _chosen_movie.summary,
            "rating": _chosen_movie.audienceRating,
            "genres": [g.tag for g in _chosen_movie.genres],
            "directors": [d.tag for d in _chosen_movie.directors],
            "writers": [w.tag for w in _chosen_movie.writers],
            "actors": [a.tag for a in _chosen_movie.actors],
            "poster": f"/api/image?path={_chosen_movie.thumb}" if _chosen_movie.thumb else None,
            "background": f"/api/image?path={_chosen_movie.art}" if _chosen_movie.art else None,
        })
    except Exception:
        app.logger.exception("get_movie failed")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/clients")
def get_clients():
    if _plex_error:
        return jsonify({"error": _plex_error}), 503
    try:
        seen = set()
        clients = []
        for c in _plex.clients():
            if c.title not in seen:
                seen.add(c.title)
                clients.append(c.title)
        for session in _plex.sessions():
            title = session.player.title
            if title not in seen:
                seen.add(title)
                clients.append(title)
        return jsonify({"clients": clients})
    except Exception:
        app.logger.exception("get_clients failed")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/play", methods=["POST"])
def play_movie():
    if _plex_error:
        return jsonify({"error": _plex_error}), 503
    if _chosen_movie is None:
        return jsonify({"error": "No movie selected — fetch a movie first"}), 400
    data = request.get_json(silent=True) or {}
    client_name = data.get("client")
    if not client_name:
        return jsonify({"error": "No client specified"}), 400
    try:
        _plex.client(client_name).playMedia(_chosen_movie)
        return jsonify({"ok": True})
    except Exception:
        app.logger.exception("play_movie failed")
        return jsonify({"error": "Internal server error"}), 500


def main():
    _connect_plex()
    port = 4000
    print(f"Random Plex Movie running at http://localhost:{port}")
    if not _in_docker():
        threading.Timer(0.5, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()
