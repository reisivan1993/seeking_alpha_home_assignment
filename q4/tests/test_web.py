import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from set_game.web import Handler, play_game


@pytest.fixture(scope="module")
def base_url():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


def get(url):
    try:
        with urllib.request.urlopen(url) as response:
            return response.status, response.headers["Content-Type"], response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.headers["Content-Type"], error.read()


def test_page_is_served(base_url):
    status, content_type, body = get(base_url + "/")
    assert status == 200
    assert content_type.startswith("text/html")
    assert b'id="play"' in body


def test_play_returns_every_round(base_url):
    status, _, body = get(base_url + "/api/play?seed=3")
    game = json.loads(body)
    assert status == 200
    assert game["seed"] == 3
    assert [r["number"] for r in game["rounds"]] == list(range(1, len(game["rounds"]) + 1))
    assert all(len(r["cards"]) == 3 for r in game["rounds"])
    assert game["set_found"] == game["rounds"][-1]["is_set"]


def test_same_seed_replays_the_same_game():
    assert play_game(11) == play_game(11)


def test_card_json_uses_readable_names():
    card = play_game(3)["rounds"][0]["cards"][0]
    assert set(card) == {"number", "shape", "shading", "color"}
    assert card["number"] in {"one", "two", "three"}


def test_without_seed_a_random_seed_is_chosen_and_returned(base_url):
    _, _, body = get(base_url + "/api/play")
    assert isinstance(json.loads(body)["seed"], int)


def test_invalid_seed_is_rejected(base_url):
    status, _, body = get(base_url + "/api/play?seed=abc")
    assert status == 400
    assert json.loads(body) == {"error": "seed must be a whole number"}


def test_unknown_path_is_404(base_url):
    status, _, _ = get(base_url + "/nope")
    assert status == 404
