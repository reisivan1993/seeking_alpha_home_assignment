"""A small local web UI: python -m set_game.web, then open http://127.0.0.1:8765

GET /                  the page (static/index.html)
GET /api/play?seed=N   plays one game and returns every round as JSON (seed optional)
"""

import argparse
import json
import logging
import random
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from set_game.card import Card
from set_game.deck import Deck
from set_game.game import Round, play

INDEX_HTML = (Path(__file__).parent / "static" / "index.html").read_bytes()

logger = logging.getLogger(__name__)


def card_to_json(card: Card) -> dict[str, str]:
    return {
        "number": card.number.name.lower(),
        "shape": card.shape.name.lower(),
        "shading": card.shading.name.lower(),
        "color": card.color.name.lower(),
    }


def play_game(seed: int | None) -> dict:
    """Play one shuffled game and describe it as JSON-ready data."""
    if seed is None:
        seed = random.SystemRandom().randrange(1_000_000)
    rounds: list[Round] = []
    result = play(Deck.shuffled(random.Random(seed)), on_round=rounds.append)
    return {
        "seed": seed,
        "set_found": result.found_set is not None,
        "rounds": [
            {
                "number": r.number,
                "cards": [card_to_json(c) for c in r.cards],
                "is_set": r.is_set,
                "cards_left": r.cards_left,
            }
            for r in rounds
        ],
        "cards_left": result.cards_left,
    }


def parse_seed(query: str) -> int | None:
    """The optional ?seed= parameter. Raises ValueError when it is not a whole number."""
    values = parse_qs(query).get("seed", [""])
    return int(values[0]) if values[0] else None


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        url = urlsplit(self.path)
        if url.path == "/":
            self._send(HTTPStatus.OK, "text/html; charset=utf-8", INDEX_HTML)
        elif url.path == "/api/play":
            try:
                seed = parse_seed(url.query)
            except ValueError:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "seed must be a whole number"})
                return
            game = play_game(seed)
            logger.info(
                "event=web_game seed=%d set_found=%s rounds=%d",
                game["seed"], str(game["set_found"]).lower(), len(game["rounds"]),
            )
            self._send_json(HTTPStatus.OK, game)
        else:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def _send_json(self, status: HTTPStatus, body: dict) -> None:
        self._send(status, "application/json", json.dumps(body).encode())

    def _send(self, status: HTTPStatus, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:  # route access logs through logging
        logger.debug("event=http_request %s", format % args)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the Set game UI on localhost.")
    parser.add_argument("--host", default="127.0.0.1", help="bind address (use 0.0.0.0 for Docker)")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="level=%(levelname)s %(message)s")
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    logger.info("event=web_started url=http://%s:%d", args.host, args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
