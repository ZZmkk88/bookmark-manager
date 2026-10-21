"""bookmark-manager: a lightweight self-hosted bookmark manager.

A clean-room re-implementation inspired by Linkding (MIT). Design notes live
in NOTES.md. Single-file FastAPI backend + SQLite + one static page.
"""
import hashlib
import html as html_lib
from contextlib import asynccontextmanager
import os
import re
import secrets
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = os.environ.get("BOOKMARK_DB_PATH", str(BASE_DIR / "data" / "bookmarks.db"))
TOKEN_TTL_SECONDS = 24 * 60 * 60
INITIAL_USERNAME = os.environ.get("BM_INITIAL_USERNAME", "admin")
INITIAL_PASSWORD = os.environ.get("BM_INITIAL_PASSWORD", "admin123")
# default bind address: localhost only, so the default credentials are never
# exposed to the LAN before the initial password is changed
HOST = os.environ.get("BM_HOST", "127.0.0.1")
MAX_URL_LENGTH = 2048
MAX_TITLE_LENGTH = 512
MAX_TAG_LENGTH = 64
ARCHIVED_PSEUDO_TAG = "linkding:bookmarks.archived"

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="bookmark-manager", lifespan=lifespan)


# ---------------------------------------------------------------------------
# small utilities
# ---------------------------------------------------------------------------

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def normalize_url(url: str) -> str:
    """Normalize a URL for duplicate detection (same rules as Linkding):
    lowercase scheme/host, strip trailing path slashes, sort query params."""
    if not url or not isinstance(url, str):
        return ""
    url = url.strip()
    if not url:
        return ""
    try:
        parsed = urllib.parse.urlparse(url)
        scheme = parsed.scheme.lower()
        netloc = parsed.hostname.lower() if parsed.hostname else ""
        port = parsed.port
        is_default_port = (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
        if port and not is_default_port:
            netloc += f":{port}"
        if parsed.username:
            auth = parsed.username
            if parsed.password:
                auth += f":{parsed.password}"
            netloc = f"{auth}@{netloc}"
        path = parsed.path.rstrip("/") if parsed.path else ""
        query = ""
        if parsed.query:
            params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
            params.sort(key=lambda x: (x[0], x[1]))
            query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        return urllib.parse.urlunparse(
            (scheme, netloc, path, parsed.params, query, parsed.fragment)
        )
    except (ValueError, AttributeError):
        return url


def sanitize_tag_name(tag_name: str) -> str:
    return tag_name.strip().replace(" ", "-")


def parse_tag_string(tag_string: str, delimiter: str = ",") -> list[str]:
    """Split a comma separated tag string, sanitize, dedupe (case-insensitive)."""
    if not tag_string:
        return []
    names = tag_string.strip().split(delimiter)
    names = [sanitize_tag_name(n) for n in names if n.strip()]
    seen = set()
    result = []
    for name in names:
        if len(name) > MAX_TAG_LENGTH:
            continue
        key = name.lower()
        if key not in seen:
            seen.add(key)
            result.append(name)
    result.sort(key=str.lower)
    return result


def validate_url(url: str) -> str:
    url = (url or "").strip()
    if not url or len(url) > MAX_URL_LENGTH:
        raise HTTPException(status_code=400, detail="网址为空或过长")
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise HTTPException(status_code=400, detail="只支持 http/https 网址")
    return url


# ---------------------------------------------------------------------------
# database
# ---------------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password: str, salt_hex: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 200_000
    ).hex()


def init_db() -> None:
    conn = get_db()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                must_change_password INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                expires_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                url TEXT NOT NULL,
                url_normalized TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                unread INTEGER NOT NULL DEFAULT 0,
                is_archived INTEGER NOT NULL DEFAULT 0,
                date_added TEXT NOT NULL,
                date_modified TEXT NOT NULL,
                UNIQUE(user_id, url_normalized)
            );
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                name TEXT NOT NULL,
                name_lower TEXT NOT NULL,
                date_added TEXT NOT NULL,
                UNIQUE(user_id, name_lower)
            );
            CREATE TABLE IF NOT EXISTS bookmark_tags (
                bookmark_id INTEGER NOT NULL REFERENCES bookmarks(id) ON DELETE CASCADE,
                tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
                PRIMARY KEY (bookmark_id, tag_id)
            );
            """
        )
        row = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()
        if row["c"] == 0:
            salt = secrets.token_hex(16)
            conn.execute(
                "INSERT INTO users (username, password_hash, salt, must_change_password, created_at)"
                " VALUES (?, ?, ?, 1, ?)",
                (INITIAL_USERNAME, hash_password(INITIAL_PASSWORD, salt), salt, iso(utcnow())),
            )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# auth
# ---------------------------------------------------------------------------

class LoginIn(BaseModel):
    username: str
    password: str


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str


def current_user(request: Request) -> sqlite3.Row:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = auth[len("Bearer "):].strip()
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id"
            " WHERE s.token = ? AND s.expires_at > ?",
            (token, time.time()),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
        return row
    finally:
        conn.close()


def active_user(request: Request, user: sqlite3.Row = Depends(current_user)) -> sqlite3.Row:
    """Business endpoints: blocked until the initial password has been changed.

    The forced password-change screen must not be bypassable via the API:
    only change-password, logout and the account info check are allowed
    while must_change_password is still set.
    """
    if user["must_change_password"]:
        if request.url.path not in ("/api/change-password", "/api/logout", "/api/me"):
            raise HTTPException(status_code=403, detail="请先修改初始密码再使用")
    return user


@app.post("/api/login")
def login(body: LoginIn):
    init_db()
    conn = get_db()
    try:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (body.username.strip(),)
        ).fetchone()
        if not user or hash_password(body.password, user["salt"]) != user["password_hash"]:
            raise HTTPException(status_code=401, detail="用户名或密码不正确")
        token = secrets.token_urlsafe(32)
        conn.execute(
            "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, user["id"], time.time() + TOKEN_TTL_SECONDS),
        )
        conn.commit()
        return {
            "token": token,
            "username": user["username"],
            "must_change_password": bool(user["must_change_password"]),
        }
    finally:
        conn.close()


@app.post("/api/logout")
def logout(request: Request, user: sqlite3.Row = Depends(current_user)):
    token = request.headers.get("Authorization", "")[len("Bearer "):].strip()
    conn = get_db()
    try:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


@app.post("/api/change-password")
def change_password(body: ChangePasswordIn, user: sqlite3.Row = Depends(current_user)):
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少 6 位")
    if hash_password(body.old_password, user["salt"]) != user["password_hash"]:
        raise HTTPException(status_code=400, detail="旧密码不正确")
    salt = secrets.token_hex(16)
    conn = get_db()
    try:
        conn.execute(
            "UPDATE users SET password_hash = ?, salt = ?, must_change_password = 0 WHERE id = ?",
            (hash_password(body.new_password, salt), salt, user["id"]),
        )
        # drop every existing session, including the initial token, so no
        # pre-change token can be reused after the password changed
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (user["id"],))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


@app.get("/api/me")
def me(user: sqlite3.Row = Depends(current_user)):
    return {
        "username": user["username"],
        "must_change_password": bool(user["must_change_password"]),
    }


# ---------------------------------------------------------------------------
# website metadata scraping (title / description), Linkding-style:
# stream the page, stop at </head>, browser-like headers, never raise.
# ---------------------------------------------------------------------------

FAKE_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml",
    "Accept-Encoding": "identity",
    "Dnt": "1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/101.0.0.0 Safari/537.36"
    ),
}
FETCH_LIMIT = 1024 * 1024


class _HeadParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_title = False
        self.title_parts: list[str] = []
        self.meta: dict[str, str] = {}

    def handle_starttag(self, tag, attrs):
        attrs = {k.lower(): (v or "") for k, v in attrs}
        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            key = attrs.get("name") or attrs.get("property")
            if key and attrs.get("content"):
                self.meta[key.lower()] = attrs["content"]

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data)


def _decode_page(raw: bytes, content_type: str) -> str:
    charset = None
    m = re.search(r'charset=["\']?([\w\-]+)', content_type or "", re.I)
    if m:
        charset = m.group(1)
    if not charset:
        m = re.search(rb"<meta[^>]+charset=[\"']?([\w\-]+)", raw[:4096], re.I)
        if m:
            charset = m.group(1).decode("ascii", "replace")
    for enc in ([charset] if charset else []) + ["utf-8"]:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", "replace")


def fetch_metadata(url: str) -> dict:
    """Fetch a page and extract title/description. Returns empty values on
    any failure instead of raising (same contract as Linkding)."""
    result = {"url": url, "title": None, "description": None}
    try:
        req = urllib.request.Request(url, headers=FAKE_HEADERS)
        chunks = []
        size = 0
        with urllib.request.urlopen(req, timeout=10) as resp:
            content_type = resp.headers.get("Content-Type", "")
            while True:
                chunk = resp.read(50 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
                joined = b"".join(chunks)
                if b"</head>" in joined.lower() or size > FETCH_LIMIT:
                    chunks = [joined]
                    break
        raw = b"".join(chunks)
        head_end = raw.lower().find(b"</head>")
        if head_end != -1:
            raw = raw[: head_end + len(b"</head>")]
        text = _decode_page(raw, content_type)
        parser = _HeadParser()
        parser.feed(text)
        title = "".join(parser.title_parts).strip() or parser.meta.get("og:title")
        description = parser.meta.get("description") or parser.meta.get("og:description")
        result["title"] = title.strip() if title else None
        result["description"] = description.strip() if description else None
    except Exception:
        pass
    return result


class FetchIn(BaseModel):
    url: str


@app.post("/api/fetch-metadata")
def fetch_metadata_api(body: FetchIn, user: sqlite3.Row = Depends(active_user)):
    url = validate_url(body.url)
    return fetch_metadata(url)


# ---------------------------------------------------------------------------
# bookmarks
# ---------------------------------------------------------------------------

class BookmarkIn(BaseModel):
    url: str
    title: str | None = None
    description: str | None = None
    notes: str | None = None
    tags: str | None = None  # comma separated, Linkding style
    unread: bool = False


class BookmarkUpdateIn(BaseModel):
    url: str | None = None
    title: str | None = None
    description: str | None = None
    notes: str | None = None
    tags: str | None = None
    unread: bool | None = None
    is_archived: bool | None = None


def _get_or_create_tag(conn: sqlite3.Connection, user_id: int, name: str) -> int:
    row = conn.execute(
        "SELECT id FROM tags WHERE user_id = ? AND name_lower = ?",
        (user_id, name.lower()),
    ).fetchone()
    if row:
        return row["id"]
    cur = conn.execute(
        "INSERT INTO tags (user_id, name, name_lower, date_added) VALUES (?, ?, ?, ?)",
        (user_id, name, name.lower(), iso(utcnow())),
    )
    return cur.lastrowid


def _set_bookmark_tags(conn: sqlite3.Connection, user_id: int, bookmark_id: int, tag_names: list[str]) -> None:
    conn.execute("DELETE FROM bookmark_tags WHERE bookmark_id = ?", (bookmark_id,))
    for name in tag_names:
        tag_id = _get_or_create_tag(conn, user_id, name)
        conn.execute(
            "INSERT OR IGNORE INTO bookmark_tags (bookmark_id, tag_id) VALUES (?, ?)",
            (bookmark_id, tag_id),
        )


def _bookmark_to_dict(conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
    tags = conn.execute(
        "SELECT t.name FROM tags t JOIN bookmark_tags bt ON bt.tag_id = t.id"
        " WHERE bt.bookmark_id = ? ORDER BY t.name_lower",
        (row["id"],),
    ).fetchall()
    return {
        "id": row["id"],
        "url": row["url"],
        "title": row["title"],
        "description": row["description"],
        "notes": row["notes"],
        "unread": bool(row["unread"]),
        "is_archived": bool(row["is_archived"]),
        "date_added": row["date_added"],
        "date_modified": row["date_modified"],
        "tags": [t["name"] for t in tags],
    }


@app.post("/api/bookmarks", status_code=201)
def create_bookmark(body: BookmarkIn, user: sqlite3.Row = Depends(active_user)):
    url = validate_url(body.url)
    normalized = normalize_url(url)
    title = (body.title or "").strip()
    description = (body.description or "").strip()
    if not title:
        meta = fetch_metadata(url)
        title = (meta.get("title") or "").strip()
        if not description:
            description = (meta.get("description") or "").strip()
    title = title[:MAX_TITLE_LENGTH]
    tag_names = parse_tag_string(body.tags or "")
    now = iso(utcnow())
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM bookmarks WHERE user_id = ? AND url_normalized = ?",
            (user["id"], normalized),
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="这个网址已经收藏过了")
        cur = conn.execute(
            "INSERT INTO bookmarks (user_id, url, url_normalized, title, description, notes,"
            " unread, is_archived, date_added, date_modified) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)",
            (user["id"], url, normalized, title, description, body.notes or "",
             1 if body.unread else 0, now, now),
        )
        bookmark_id = cur.lastrowid
        _set_bookmark_tags(conn, user["id"], bookmark_id, tag_names)
        conn.commit()
        row = conn.execute("SELECT * FROM bookmarks WHERE id = ?", (bookmark_id,)).fetchone()
        return _bookmark_to_dict(conn, row)
    finally:
        conn.close()


@app.get("/api/bookmarks")
def list_bookmarks(
    q: str = "",
    tag: str = "",
    archived: str = "0",
    unread: str = "",
    user: sqlite3.Row = Depends(active_user),
):
    conn = get_db()
    try:
        sql = "SELECT DISTINCT b.* FROM bookmarks b"
        joins = []
        where = ["b.user_id = ?"]
        params: list = [user["id"]]
        if archived == "0":
            where.append("b.is_archived = 0")
        elif archived == "1":
            where.append("b.is_archived = 1")
        if unread in ("1", "true"):
            where.append("b.unread = 1")
        if tag:
            joins.append("JOIN bookmark_tags bt ON bt.bookmark_id = b.id JOIN tags tg ON tg.id = bt.tag_id")
            where.append("tg.name_lower = ?")
            params.append(sanitize_tag_name(tag).lower())
        if q:
            joins.append("LEFT JOIN bookmark_tags bq ON bq.bookmark_id = b.id LEFT JOIN tags tq ON tq.id = bq.tag_id")
            like = f"%{q}%"
            where.append(
                "(b.title LIKE ? OR b.url LIKE ? OR b.description LIKE ? OR b.notes LIKE ? OR tq.name LIKE ?)"
            )
            params.extend([like, like, like, like, like])
        sql += " " + " ".join(joins) + " WHERE " + " AND ".join(where)
        sql += " ORDER BY b.date_added DESC, b.id DESC"
        rows = conn.execute(sql, params).fetchall()
        return {"bookmarks": [_bookmark_to_dict(conn, r) for r in rows], "total": len(rows)}
    finally:
        conn.close()


def _load_bookmark(conn: sqlite3.Connection, user_id: int, bookmark_id: int) -> sqlite3.Row:
    row = conn.execute(
        "SELECT * FROM bookmarks WHERE id = ? AND user_id = ?", (bookmark_id, user_id)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="书签不存在")
    return row


@app.get("/api/bookmarks/{bookmark_id}")
def get_bookmark(bookmark_id: int, user: sqlite3.Row = Depends(active_user)):
    conn = get_db()
    try:
        return _bookmark_to_dict(conn, _load_bookmark(conn, user["id"], bookmark_id))
    finally:
        conn.close()


@app.put("/api/bookmarks/{bookmark_id}")
def update_bookmark(bookmark_id: int, body: BookmarkUpdateIn, user: sqlite3.Row = Depends(active_user)):
    conn = get_db()
    try:
        row = _load_bookmark(conn, user["id"], bookmark_id)
        url = row["url"]
        normalized = row["url_normalized"]
        if body.url is not None:
            url = validate_url(body.url)
            normalized = normalize_url(url)
            clash = conn.execute(
                "SELECT id FROM bookmarks WHERE user_id = ? AND url_normalized = ? AND id != ?",
                (user["id"], normalized, bookmark_id),
            ).fetchone()
            if clash:
                raise HTTPException(status_code=409, detail="这个网址已经收藏过了")
        conn.execute(
            "UPDATE bookmarks SET url = ?, url_normalized = ?, title = ?, description = ?,"
            " notes = ?, unread = ?, is_archived = ?, date_modified = ? WHERE id = ?",
            (
                url,
                normalized,
                (body.title if body.title is not None else row["title"])[:MAX_TITLE_LENGTH],
                body.description if body.description is not None else row["description"],
                body.notes if body.notes is not None else row["notes"],
                (1 if body.unread else 0) if body.unread is not None else row["unread"],
                (1 if body.is_archived else 0) if body.is_archived is not None else row["is_archived"],
                iso(utcnow()),
                bookmark_id,
            ),
        )
        if body.tags is not None:
            _set_bookmark_tags(conn, user["id"], bookmark_id, parse_tag_string(body.tags))
        conn.commit()
        return _bookmark_to_dict(conn, _load_bookmark(conn, user["id"], bookmark_id))
    finally:
        conn.close()


@app.delete("/api/bookmarks/{bookmark_id}")
def delete_bookmark(bookmark_id: int, user: sqlite3.Row = Depends(active_user)):
    conn = get_db()
    try:
        _load_bookmark(conn, user["id"], bookmark_id)
        conn.execute("DELETE FROM bookmark_tags WHERE bookmark_id = ?", (bookmark_id,))
        conn.execute("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


@app.get("/api/tags")
def list_tags(user: sqlite3.Row = Depends(active_user)):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT t.name, COUNT(bt.bookmark_id) AS count FROM tags t"
            " LEFT JOIN bookmark_tags bt ON bt.tag_id = t.id"
            " WHERE t.user_id = ? GROUP BY t.id ORDER BY t.name_lower",
            (user["id"],),
        ).fetchall()
        return {"tags": [{"name": r["name"], "count": r["count"]} for r in rows]}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Netscape bookmark file import / export (format compatible with Linkding
# and with browser bookmark exports)
# ---------------------------------------------------------------------------

class NetscapeParser(HTMLParser):
    """Parses Netscape bookmark HTML. Mirrors the format semantics that
    Linkding uses: <A> attributes carry metadata, link text is the title,
    a following <DD> holds the description (with [linkding-notes] block)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.bookmarks: list[dict] = []
        self._pending: dict | None = None
        self._in_a = False
        self._in_dd = False

    def _flush(self):
        if self._pending is not None:
            self.bookmarks.append(self._pending)
            self._pending = None

    def handle_starttag(self, tag, attrs):
        if tag == "dt":
            self._flush()
        elif tag == "a":
            self._flush()
            attrs = {k.lower(): (v or "") for k, v in attrs}
            tag_names = parse_tag_string(attrs.get("tags", ""))
            archived = ARCHIVED_PSEUDO_TAG in tag_names
            if archived:
                tag_names.remove(ARCHIVED_PSEUDO_TAG)
            self._pending = {
                "href": attrs.get("href", ""),
                "title": "",
                "description": "",
                "notes": "",
                "add_date": attrs.get("add_date", ""),
                "last_modified": attrs.get("last_modified", ""),
                "tag_names": tag_names,
                "unread": attrs.get("toread", "") == "1",
                "is_archived": archived,
            }
            self._in_a = True
        elif tag == "dd":
            self._in_dd = True

    def handle_endtag(self, tag):
        if tag == "a":
            self._in_a = False
        elif tag == "dd":
            self._in_dd = False
        elif tag == "dl":
            self._flush()

    def handle_data(self, data):
        if self._pending is None:
            return
        if self._in_a:
            self._pending["title"] += data
        elif self._in_dd:
            self._pending["description"] += data

    def close(self):
        super().close()
        self._flush()
        # split notes out of descriptions, tidy whitespace
        for bm in self.bookmarks:
            desc = bm["description"].strip()
            if "[linkding-notes]" in desc:
                before, rest = desc.split("[linkding-notes]", 1)
                notes = rest.split("[/linkding-notes]")[0]
                bm["notes"] = notes.strip()
                desc = before.strip()
            bm["description"] = desc
            bm["title"] = bm["title"].strip()


def _epoch_to_iso(value: str) -> str | None:
    try:
        ts = int(value)
        if ts <= 0:
            return None
        return iso(datetime.fromtimestamp(ts, tz=timezone.utc))
    except (TypeError, ValueError):
        return None


def import_netscape(html_text: str, user_id: int) -> dict:
    parser = NetscapeParser()
    parser.feed(html_text)
    parser.close()
    result = {"total": 0, "success": 0, "failed": 0, "skipped": 0}
    conn = get_db()
    try:
        seen_in_file: set[str] = set()
        for item in parser.bookmarks:
            result["total"] += 1
            try:
                href = (item["href"] or "").strip()
                parsed = urllib.parse.urlparse(href)
                if parsed.scheme not in ("http", "https") or not parsed.hostname:
                    result["failed"] += 1
                    continue
                normalized = normalize_url(href)
                if normalized in seen_in_file:
                    # same URL twice inside one file: genuinely skipped, not failed
                    result["skipped"] += 1
                    continue
                seen_in_file.add(normalized)
                now = iso(utcnow())
                date_added = _epoch_to_iso(item["add_date"]) or now
                date_modified = _epoch_to_iso(item["last_modified"]) or date_added
                existing = conn.execute(
                    "SELECT id FROM bookmarks WHERE user_id = ? AND url_normalized = ?",
                    (user_id, normalized),
                ).fetchone()
                if existing:
                    bookmark_id = existing["id"]
                    conn.execute(
                        "UPDATE bookmarks SET url = ?, title = ?, description = ?, notes = ?,"
                        " unread = ?, is_archived = ?, date_added = ?, date_modified = ? WHERE id = ?",
                        (href, item["title"][:MAX_TITLE_LENGTH], item["description"], item["notes"],
                         1 if item["unread"] else 0, 1 if item["is_archived"] else 0,
                         date_added, date_modified, bookmark_id),
                    )
                else:
                    cur = conn.execute(
                        "INSERT INTO bookmarks (user_id, url, url_normalized, title, description,"
                        " notes, unread, is_archived, date_added, date_modified)"
                        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (user_id, href, normalized, item["title"][:MAX_TITLE_LENGTH],
                         item["description"], item["notes"], 1 if item["unread"] else 0,
                         1 if item["is_archived"] else 0, date_added, date_modified),
                    )
                    bookmark_id = cur.lastrowid
                _set_bookmark_tags(conn, user_id, bookmark_id, item["tag_names"])
                result["success"] += 1
            except Exception:
                result["failed"] += 1
        conn.commit()
        return result
    finally:
        conn.close()


@app.post("/api/import")
async def import_api(file: UploadFile = File(...), user: sqlite3.Row = Depends(active_user)):
    raw = await file.read()
    if len(raw) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件过大（上限 20MB）")
    html_text = raw.decode("utf-8", "replace")
    return import_netscape(html_text, user["id"])


def export_netscape(user_id: int) -> str:
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM bookmarks WHERE user_id = ? ORDER BY date_added, id", (user_id,)
        ).fetchall()
        doc = [
            "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
            '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
            "<TITLE>Bookmarks</TITLE>",
            "<H1>Bookmarks</H1>",
            "<DL><p>",
        ]
        for row in rows:
            bm = _bookmark_to_dict(conn, row)
            tag_names = list(bm["tags"])
            if bm["is_archived"]:
                tag_names.append(ARCHIVED_PSEUDO_TAG)
            tags = ",".join(html_lib.escape(t, quote=True) for t in tag_names)
            desc = html_lib.escape(bm["description"] or "")
            if bm["notes"]:
                desc += f"[linkding-notes]{html_lib.escape(bm['notes'])}[/linkding-notes]"
            added = int(datetime.fromisoformat(bm["date_added"]).timestamp())
            modified = int(datetime.fromisoformat(bm["date_modified"]).timestamp())
            toread = "1" if bm["unread"] else "0"
            doc.append(
                f'<DT><A HREF="{html_lib.escape(bm["url"], quote=True)}" ADD_DATE="{added}"'
                f' LAST_MODIFIED="{modified}" PRIVATE="1" TOREAD="{toread}" TAGS="{tags}">'
                f'{html_lib.escape(bm["title"] or "")}</A>'
            )
            if desc:
                doc.append(f"<DD>{desc}")
        doc.append("</DL><p>")
        return "\r\n".join(doc)
    finally:
        conn.close()


@app.get("/api/export")
def export_api(user: sqlite3.Row = Depends(active_user)):
    content = export_netscape(user["id"])
    return Response(
        content=content,
        media_type="text/html; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="bookmarks.html"'},
    )


# ---------------------------------------------------------------------------
# frontend (single page)
# ---------------------------------------------------------------------------

@app.get("/")
def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/health")
def health():
    return {"ok": True, "app": "bookmark-manager"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=HOST, port=int(os.environ.get("PORT", "8000")))
