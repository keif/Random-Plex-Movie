import pytest
from unittest.mock import MagicMock
import randomPlexMovie as mod


def _make_movie():
    m = MagicMock()
    m.title = "The Matrix"
    m.year = 1999
    m.duration = 8160000  # 2h 16m in ms
    m.summary = "A hacker discovers reality is a simulation."
    m.audienceRating = 8.7
    m.genres = [MagicMock(tag="Action"), MagicMock(tag="Sci-Fi")]
    m.directors = [MagicMock(tag="Lana Wachowski")]
    m.writers = [MagicMock(tag="Lilly Wachowski")]
    m.actors = [MagicMock(tag="Keanu Reeves"), MagicMock(tag="Laurence Fishburne")]
    m.thumb = "/library/metadata/1/thumb/123"
    m.art = "/library/metadata/1/art/456"
    return m


def _make_session(title):
    session = MagicMock()
    session.player.title = title
    return session


@pytest.fixture(autouse=True)
def mock_plex(monkeypatch):
    server = MagicMock()
    section = MagicMock()
    section.search.return_value = [_make_movie()]
    server.clients.return_value = [MagicMock(title="Living Room TV")]
    server.sessions.return_value = []
    monkeypatch.setattr(mod, "_plex", server)
    monkeypatch.setattr(mod, "_movies", section)
    monkeypatch.setattr(mod, "_plex_error", None)
    monkeypatch.setattr(mod, "_chosen_movie", None)
    monkeypatch.setattr(mod, "_plex_library", "Movies")
    return server, section


@pytest.fixture
def client():
    mod.app.config["TESTING"] = True
    with mod.app.test_client() as c:
        yield c


class TestConnectPlex:
    def test_uses_configured_library_name(self, monkeypatch):
        server = MagicMock()
        monkeypatch.setattr(mod, "_plex_library", "4K Movies")
        monkeypatch.setattr(mod, "_plex_error", None)
        monkeypatch.setattr("randomPlexMovie.PlexServer", lambda *a, **kw: server)
        mod._connect_plex()
        server.library.section.assert_called_once_with("4K Movies")


class TestProxyImage:
    def test_rejects_non_library_path(self, client):
        r = client.get("/api/image?path=/etc/passwd")
        assert r.status_code == 400

    def test_rejects_path_traversal(self, client):
        r = client.get("/api/image?path=/library/../../etc/passwd")
        assert r.status_code == 400

    def test_rejects_path_with_query_string(self, client):
        r = client.get("/api/image?path=/library/metadata/1/thumb/123?injected=1")
        assert r.status_code == 400

    def test_proxies_library_path(self, client, monkeypatch):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"IMGDATA"
        mock_resp.headers.get.return_value = "image/jpeg"
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        monkeypatch.setattr(mod, "urlopen", lambda *a, **kw: mock_resp)
        r = client.get("/api/image?path=/library/metadata/1/thumb/123")
        assert r.status_code == 200
        assert r.data == b"IMGDATA"

    def test_returns_502_on_fetch_failure(self, client, monkeypatch):
        monkeypatch.setattr(mod, "urlopen", lambda *a, **kw: (_ for _ in ()).throw(Exception("timeout")))
        r = client.get("/api/image?path=/library/metadata/1/thumb/123")
        assert r.status_code == 502


class TestGetStatus:
    def test_ok_when_plex_reachable(self, client):
        r = client.get("/api/status")
        assert r.status_code == 200
        assert r.get_json() == {"ok": True}

    def test_not_ok_when_plex_error(self, client, monkeypatch):
        monkeypatch.setattr(mod, "_plex_error", "Connection refused")
        r = client.get("/api/status")
        assert r.status_code == 200
        data = r.get_json()
        assert data["ok"] is False
        assert "error" in data

    def test_not_ok_when_query_raises(self, client, mock_plex):
        server, _ = mock_plex
        server.query.side_effect = Exception("timeout")
        r = client.get("/api/status")
        assert r.status_code == 200
        data = r.get_json()
        assert data["ok"] is False
        assert "error" in data


class TestGetMovie:
    def test_returns_full_movie_data(self, client):
        r = client.get("/api/movie")
        assert r.status_code == 200
        data = r.get_json()
        assert data["title"] == "The Matrix"
        assert data["year"] == 1999
        assert data["duration_hours"] == 2
        assert data["duration_minutes"] == 16
        assert data["summary"] == "A hacker discovers reality is a simulation."
        assert data["rating"] == 8.7
        assert data["genres"] == ["Action", "Sci-Fi"]
        assert data["directors"] == ["Lana Wachowski"]
        assert data["writers"] == ["Lilly Wachowski"]
        assert data["actors"] == ["Keanu Reeves", "Laurence Fishburne"]
        assert data["poster"] == "/api/image?path=/library/metadata/1/thumb/123"
        assert data["background"] == "/api/image?path=/library/metadata/1/art/456"

    def test_sets_chosen_movie_global(self, client):
        client.get("/api/movie")
        assert mod._chosen_movie is not None

    def test_no_unwatched_returns_404(self, client, mock_plex):
        _, section = mock_plex
        section.search.return_value = []
        r = client.get("/api/movie")
        assert r.status_code == 404
        assert "error" in r.get_json()

    def test_plex_error_returns_503(self, client, monkeypatch):
        monkeypatch.setattr(mod, "_plex_error", "Connection refused")
        r = client.get("/api/movie")
        assert r.status_code == 503
        assert r.get_json()["error"] == "Connection refused"

    def test_plex_exception_returns_500(self, client, mock_plex):
        _, section = mock_plex
        section.search.side_effect = Exception("search failed")
        r = client.get("/api/movie")
        assert r.status_code == 500
        assert "error" in r.get_json()


class TestGetClients:
    def test_returns_client_names(self, client):
        r = client.get("/api/clients")
        assert r.status_code == 200
        assert r.get_json() == {"clients": ["Living Room TV"]}

    def test_empty_list_is_valid(self, client, mock_plex):
        server, _ = mock_plex
        server.clients.return_value = []
        r = client.get("/api/clients")
        assert r.status_code == 200
        assert r.get_json() == {"clients": []}

    def test_includes_session_players(self, client, mock_plex):
        server, _ = mock_plex
        server.clients.return_value = []
        server.sessions.return_value = [_make_session("Plex Web — Chrome")]
        r = client.get("/api/clients")
        assert r.status_code == 200
        assert r.get_json() == {"clients": ["Plex Web — Chrome"]}

    def test_deduplicates_gdm_and_session_clients(self, client, mock_plex):
        server, _ = mock_plex
        server.sessions.return_value = [_make_session("Living Room TV")]
        r = client.get("/api/clients")
        assert r.status_code == 200
        assert r.get_json() == {"clients": ["Living Room TV"]}

    def test_plex_error_returns_503(self, client, monkeypatch):
        monkeypatch.setattr(mod, "_plex_error", "Connection refused")
        r = client.get("/api/clients")
        assert r.status_code == 503

    def test_exception_returns_500(self, client, mock_plex):
        server, _ = mock_plex
        server.clients.side_effect = Exception("network error")
        r = client.get("/api/clients")
        assert r.status_code == 500
        assert r.get_json() == {"error": "Internal server error"}


class TestPlayMovie:
    def test_plays_on_named_client(self, client, monkeypatch, mock_plex):
        server, _ = mock_plex
        monkeypatch.setattr(mod, "_chosen_movie", _make_movie())
        r = client.post("/api/play", json={"client": "Living Room TV"})
        assert r.status_code == 200
        assert r.get_json() == {"ok": True}
        server.client.assert_called_once_with("Living Room TV")

    def test_no_movie_selected_returns_400(self, client):
        r = client.post("/api/play", json={"client": "Living Room TV"})
        assert r.status_code == 400
        assert "error" in r.get_json()

    def test_missing_client_field_returns_400(self, client, monkeypatch):
        monkeypatch.setattr(mod, "_chosen_movie", _make_movie())
        r = client.post("/api/play", json={})
        assert r.status_code == 400
        assert "error" in r.get_json()

    def test_plex_error_returns_503(self, client, monkeypatch):
        monkeypatch.setattr(mod, "_plex_error", "Connection refused")
        monkeypatch.setattr(mod, "_chosen_movie", _make_movie())
        r = client.post("/api/play", json={"client": "Living Room TV"})
        assert r.status_code == 503

    def test_play_exception_returns_500(self, client, monkeypatch, mock_plex):
        server, _ = mock_plex
        monkeypatch.setattr(mod, "_chosen_movie", _make_movie())
        server.client.return_value.playMedia.side_effect = Exception("play failed")
        r = client.post("/api/play", json={"client": "Living Room TV"})
        assert r.status_code == 500
        assert "error" in r.get_json()
