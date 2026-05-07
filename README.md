# Local URL Shortener API

A minimal REST API for shortening links, built with Python standard library and SQLite.

## What this project demonstrates

- Backend routing without external frameworks.
- Input validation and JSON API responses.
- Persistent storage with SQLite.
- Redirect flow and simple analytics (visit counter).

## Stack

- Python 3.10+
- `http.server` (HTTP server)
- `sqlite3` (database)

## Files

- `app.py` - API server + database logic.
- `urls.db` - auto-generated SQLite database.

## Run locally

```bash
cd local-url-shortener
python3 app.py
```

Server URL: `http://127.0.0.1:8080`

## Endpoints

### `POST /api/shorten`
Create a short URL.

Request:

```json
{
  "url": "https://example.com/page"
}
```

Response (`201`):

```json
{
  "message": "Short URL created",
  "short_code": "aB3xY9",
  "short_url": "http://127.0.0.1:8080/aB3xY9",
  "long_url": "https://example.com/page"
}
```

### `GET /{short_code}`
Redirects to the original URL (`302 Found`).

### `GET /api/urls`
Returns the latest records with visits and creation time.

## Test commands

```bash
curl -X POST http://127.0.0.1:8080/api/shorten \
  -H "Content-Type: application/json" \
  -d '{"url":"https://github.com"}'

curl http://127.0.0.1:8080/api/urls
```

## Possible improvements

- Custom aliases.
- Link expiration dates.
- Auth for admin operations.
- Unit and integration tests.
