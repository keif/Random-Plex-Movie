import configparser
import re
import threading
import webbrowser
from random import choice

from flask import Flask, jsonify, request, send_from_directory
from plexapi.server import PlexServer

app = Flask(__name__, static_folder="web", static_url_path="")

_config = configparser.ConfigParser()
_config.read("config/config.ini")

_plex = None
_movies = None
_plex_error = None
_chosen_movie = None


def _scrub_token(text):
    return re.sub(r"X-Plex-Token=[^&\s\"']+", "X-Plex-Token=REDACTED", str(text))


def _connect_plex():
    global _plex, _movies, _plex_error
    try:
        _plex = PlexServer(_config["auth"]["baseurl"], _config["auth"]["token"])
        _movies = _plex.library.section("Movies")
    except Exception as exc:
        _plex_error = _scrub_token(exc)


@app.route("/")
def index():
    return send_from_directory("web", "index.html")


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
            "poster": _chosen_movie.posterUrl,
            "background": _chosen_movie.artUrl,
        })
    except Exception:
        app.logger.exception("get_movie failed")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/clients")
def get_clients():
    if _plex_error:
        return jsonify({"error": _plex_error}), 503
    try:
        return jsonify({"clients": [c.title for c in _plex.clients()]})
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
    threading.Timer(0.5, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    print(f"Random Plex Movie running at http://localhost:{port}")
    app.run(port=port, debug=False)


if __name__ == "__main__":
    main()
