#!/usr/bin/env python3
import json
import re
import sqlite3
import string
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from random import choices
from urllib.parse import urlparse

DB_PATH = Path(__file__).with_name("urls.db")
HOST = "127.0.0.1"
PORT = 8080
SHORT_CODE_LEN = 6
ALPHABET = string.ascii_letters + string.digits


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                short_code TEXT UNIQUE NOT NULL,
                long_url TEXT NOT NULL,
                visits INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if not parsed.netloc:
        return False
    return True


def generate_code() -> str:
    return "".join(choices(ALPHABET, k=SHORT_CODE_LEN))


def create_short_url(long_url: str) -> str:
    with sqlite3.connect(DB_PATH) as conn:
        while True:
            code = generate_code()
            try:
                conn.execute(
                    "INSERT INTO urls (short_code, long_url) VALUES (?, ?)",
                    (code, long_url),
                )
                conn.commit()
                return code
            except sqlite3.IntegrityError:
                continue


def fetch_long_url(code: str):
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT long_url FROM urls WHERE short_code = ?", (code,)
        ).fetchone()
        if row is None:
            return None
        conn.execute(
            "UPDATE urls SET visits = visits + 1 WHERE short_code = ?", (code,)
        )
        conn.commit()
        return row[0]


def list_urls(limit: int = 20):
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            """
            SELECT short_code, long_url, visits, created_at
            FROM urls
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [
        {
            "short_code": r[0],
            "long_url": r[1],
            "visits": r[2],
            "created_at": r[3],
        }
        for r in rows
    ]


class URLShortenerHandler(BaseHTTPRequestHandler):
    def _read_json(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length == 0:
            return None
        body = self.rfile.read(content_length)
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            return None

    def _send_json(self, payload: dict, status: int = HTTPStatus.OK):
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_POST(self):
        if self.path != "/api/shorten":
            self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return

        data = self._read_json()
        if not data or "url" not in data:
            self._send_json({"error": "Missing 'url' field"}, HTTPStatus.BAD_REQUEST)
            return

        long_url = data["url"].strip()
        if not is_valid_url(long_url):
            self._send_json({"error": "Invalid URL"}, HTTPStatus.BAD_REQUEST)
            return

        code = create_short_url(long_url)
        short_url = f"http://{HOST}:{PORT}/{code}"
        self._send_json(
            {
                "message": "Short URL created",
                "short_code": code,
                "short_url": short_url,
                "long_url": long_url,
            },
            HTTPStatus.CREATED,
        )

    def do_GET(self):
        if self.path == "/api/urls":
            self._send_json({"items": list_urls()})
            return

        match = re.fullmatch(r"/([A-Za-z0-9]{6})", self.path)
        if match:
            code = match.group(1)
            long_url = fetch_long_url(code)
            if long_url is None:
                self._send_json({"error": "Short code not found"}, HTTPStatus.NOT_FOUND)
                return

            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", long_url)
            self.end_headers()
            return

        self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

    def log_message(self, format, *args):
        return


def run_server(host: str = HOST, port: int = PORT):
    init_db()
    server = ThreadingHTTPServer((host, port), URLShortenerHandler)
    print(f"Server running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
