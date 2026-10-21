"""Automated tests for bookmark-manager. Run: .venv/bin/python -m pytest tests/ -q"""
import os
import sqlite3
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

_tmp = tempfile.mkdtemp(prefix="bm-test-")
os.environ["BOOKMARK_DB_PATH"] = os.path.join(_tmp, "test.db")
os.environ["BM_INITIAL_USERNAME"] = "admin"
os.environ["BM_INITIAL_PASSWORD"] = "admin123"

import app as appmod  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(appmod.app) as c:
        yield c


def do_login(client, password="admin123"):
    res = client.post("/api/login", json={"username": "admin", "password": password})
    assert res.status_code == 200, res.text
    return res.json()


@pytest.fixture()
def auth(client):
    # fresh usable token per test: rotate the password to the same value once
    # to clear the forced-change flag (change-password is always allowed)
    first = do_login(client)
    h1 = {"Authorization": f"Bearer {first['token']}"}
    res = client.post(
        "/api/change-password",
        json={"old_password": "admin123", "new_password": "admin123"},
        headers=h1,
    )
    assert res.status_code == 200
    data = do_login(client)
    assert data["must_change_password"] is False
    return {"Authorization": f"Bearer {data['token']}"}


# ---------------------------------------------------------------- auth ----

def test_login_wrong_password(client):
    res = client.post("/api/login", json={"username": "admin", "password": "nope"})
    assert res.status_code == 401


def test_login_ok_and_must_change(client):
    data = do_login(client)
    assert data["token"]
    assert data["must_change_password"] is True


def test_unauthenticated_rejected(client):
    assert client.get("/api/bookmarks").status_code == 401
    assert client.get("/api/me").status_code == 401


def test_change_password(client, auth):
    res = client.post(
        "/api/change-password",
        json={"old_password": "admin123", "new_password": "newpass456"},
        headers=auth,
    )
    assert res.status_code == 200
    # all sessions are dropped on password change: the old token is dead
    assert client.get("/api/me", headers=auth).status_code == 401
    data = do_login(client, "newpass456")
    assert data["must_change_password"] is False
    # restore for other tests
    res = client.post(
        "/api/change-password",
        json={"old_password": "newpass456", "new_password": "admin123"},
        headers={"Authorization": f"Bearer {data['token']}"},
    )
    assert res.status_code == 200


def test_token_expiry(client):
    data = do_login(client)
    conn = sqlite3.connect(os.environ["BOOKMARK_DB_PATH"])
    conn.execute("UPDATE sessions SET expires_at = 0 WHERE token = ?", (data["token"],))
    conn.commit()
    conn.close()
    res = client.get("/api/me", headers={"Authorization": f"Bearer {data['token']}"})
    assert res.status_code == 401


# ------------------------------------------------------------ bookmarks ----

def test_create_with_title_no_scrape(client, auth, monkeypatch):
    def boom(url):  # must not be called when title is provided
        raise AssertionError("scrape should not run")

    monkeypatch.setattr(appmod, "fetch_metadata", boom)
    res = client.post(
        "/api/bookmarks",
        json={"url": "https://example.com/manual", "title": "手动标题", "description": "手填描述"},
        headers=auth,
    )
    assert res.status_code == 201, res.text
    bm = res.json()
    assert bm["title"] == "手动标题"
    assert bm["description"] == "手填描述"


def test_create_uses_scraper_when_title_missing(client, auth, monkeypatch):
    monkeypatch.setattr(
        appmod, "fetch_metadata",
        lambda url: {"url": url, "title": "抓到的标题", "description": "抓到的描述"},
    )
    res = client.post("/api/bookmarks", json={"url": "https://example.com/auto"}, headers=auth)
    assert res.status_code == 201
    bm = res.json()
    assert bm["title"] == "抓到的标题"
    assert bm["description"] == "抓到的描述"


def test_create_duplicate_normalized_url_409(client, auth):
    res = client.post(
        "/api/bookmarks",
        json={"url": "https://example.com/manual/", "title": "重复"},
        headers=auth,
    )
    assert res.status_code == 409


def test_create_invalid_url(client, auth):
    res = client.post("/api/bookmarks", json={"url": "javascript:alert(1)", "title": "x"}, headers=auth)
    assert res.status_code == 400
    res = client.post("/api/bookmarks", json={"url": "not-a-url", "title": "x"}, headers=auth)
    assert res.status_code == 400


def test_tag_sanitization(client, auth):
    res = client.post(
        "/api/bookmarks",
        json={"url": "https://example.com/tags", "title": "标签测试",
              "tags": "Web Dev, python, PYTHON,  教程 ,web dev"},
        headers=auth,
    )
    assert res.status_code == 201
    tags = res.json()["tags"]
    # spaces -> '-', case-insensitive dedupe, sorted by lower
    assert tags == ["python", "Web-Dev", "教程"]


def test_list_and_search(client, auth):
    res = client.get("/api/bookmarks", headers=auth)
    assert res.status_code == 200
    assert res.json()["total"] >= 3
    # keyword in title
    res = client.get("/api/bookmarks", params={"q": "手动"}, headers=auth)
    assert any(b["title"] == "手动标题" for b in res.json()["bookmarks"])
    # keyword in url
    res = client.get("/api/bookmarks", params={"q": "example.com/auto"}, headers=auth)
    assert res.json()["total"] == 1
    # keyword matching a tag name
    res = client.get("/api/bookmarks", params={"q": "教程"}, headers=auth)
    assert res.json()["total"] == 1


def test_tag_filter(client, auth):
    res = client.get("/api/bookmarks", params={"tag": "Python"}, headers=auth)
    assert res.json()["total"] == 1
    assert res.json()["bookmarks"][0]["url"] == "https://example.com/tags"


def test_update_bookmark(client, auth):
    res = client.get("/api/bookmarks", params={"q": "标签测试"}, headers=auth)
    bm_id = res.json()["bookmarks"][0]["id"]
    res = client.put(
        f"/api/bookmarks/{bm_id}",
        json={"title": "标签测试改", "unread": True, "tags": "新标签"},
        headers=auth,
    )
    assert res.status_code == 200
    bm = res.json()
    assert bm["title"] == "标签测试改"
    assert bm["unread"] is True
    assert bm["tags"] == ["新标签"]
    res = client.get("/api/bookmarks", params={"unread": "1"}, headers=auth)
    assert any(b["id"] == bm_id for b in res.json()["bookmarks"])


def test_archive_filter(client, auth):
    res = client.get("/api/bookmarks", params={"q": "抓到的标题"}, headers=auth)
    bm_id = res.json()["bookmarks"][0]["id"]
    res = client.put(f"/api/bookmarks/{bm_id}", json={"is_archived": True}, headers=auth)
    assert res.json()["is_archived"] is True
    res = client.get("/api/bookmarks", headers=auth)
    assert all(not b["is_archived"] for b in res.json()["bookmarks"])
    res = client.get("/api/bookmarks", params={"archived": "1"}, headers=auth)
    assert any(b["id"] == bm_id for b in res.json()["bookmarks"])


def test_delete_bookmark(client, auth):
    res = client.post(
        "/api/bookmarks", json={"url": "https://example.com/todelete", "title": "待删"}, headers=auth
    )
    bm_id = res.json()["id"]
    res = client.delete(f"/api/bookmarks/{bm_id}", headers=auth)
    assert res.status_code == 200
    assert client.get(f"/api/bookmarks/{bm_id}", headers=auth).status_code == 404


def test_tags_endpoint(client, auth):
    res = client.get("/api/tags", headers=auth)
    names = {t["name"] for t in res.json()["tags"]}
    assert "新标签" in names


# -------------------------------------------------------------- scraping ----

FAKE_PAGE = """<!DOCTYPE html><html><head>
<title>真实抓取标题</title>
<meta name="description" content="真实抓取描述">
</head><body>hello</body></html>"""

OG_PAGE = """<!DOCTYPE html><html><head>
<meta property="og:title" content="OG标题">
<meta property="og:description" content="OG描述">
</head><body>x</body></html>"""


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = OG_PAGE if self.path == "/og" else FAKE_PAGE
        raw = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *a):
        pass


@pytest.fixture(scope="module")
def local_server():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def test_fetch_metadata_real_http(local_server):
    meta = appmod.fetch_metadata(local_server + "/page")
    assert meta["title"] == "真实抓取标题"
    assert meta["description"] == "真实抓取描述"


def test_fetch_metadata_og_fallback(local_server):
    meta = appmod.fetch_metadata(local_server + "/og")
    assert meta["title"] == "OG标题"
    assert meta["description"] == "OG描述"


def test_fetch_metadata_failure_is_quiet():
    meta = appmod.fetch_metadata("http://127.0.0.1:1/unreachable")
    assert meta["title"] is None and meta["description"] is None


# ---------------------------------------------------------------- import ----

NETSCAPE_SAMPLE = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><H3 ADD_DATE="1700000000">开发</H3>
    <DL><p>
        <DT><A HREF="https://example.com/a" ADD_DATE="1700000100" LAST_MODIFIED="1700000200" TAGS="dev,python" TOREAD="1">示例甲</A>
        <DD>甲的描述[linkding-notes]甲的备注[/linkding-notes]
        <DT><A HREF="https://example.org/b" ADD_DATE="1700000300" TAGS="linkding:bookmarks.archived,read">示例乙</A>
    </DL><p>
    <DT><A HREF="https://example.com/a/" ADD_DATE="1700000400">文件内重复</A>
    <DT><A HREF="javascript:void(0)">坏链接</A>
</DL><p>
"""


def test_import_netscape(client, auth):
    res = client.post(
        "/api/import",
        files={"file": ("bookmarks.html", NETSCAPE_SAMPLE.encode("utf-8"), "text/html")},
        headers=auth,
    )
    assert res.status_code == 200, res.text
    result = res.json()
    assert result == {"total": 4, "success": 2, "failed": 2}, result
    res = client.get("/api/bookmarks", params={"q": "示例甲"}, headers=auth)
    bm = res.json()["bookmarks"][0]
    assert bm["unread"] is True
    assert bm["description"] == "甲的描述"
    assert bm["notes"] == "甲的备注"
    assert set(bm["tags"]) == {"dev", "python"}
    assert bm["date_added"].startswith("2023-11-14")
    # archived one lives in the archive view, without the pseudo tag
    res = client.get("/api/bookmarks", params={"archived": "1", "q": "示例乙"}, headers=auth)
    bm = res.json()["bookmarks"][0]
    assert bm["is_archived"] is True
    assert bm["tags"] == ["read"]


def test_export_and_roundtrip(client, auth):
    res = client.get("/api/export", headers=auth)
    assert res.status_code == 200
    text = res.text
    assert "NETSCAPE-Bookmark-file-1" in text
    assert "https://example.com/a" in text
    assert "linkding:bookmarks.archived" in text  # archived encoded as pseudo tag

    # wipe, then re-import the export: everything comes back
    conn = sqlite3.connect(os.environ["BOOKMARK_DB_PATH"])
    conn.execute("DELETE FROM bookmark_tags")
    conn.execute("DELETE FROM bookmarks")
    conn.commit()
    conn.close()
    res = client.post(
        "/api/import",
        files={"file": ("roundtrip.html", text.encode("utf-8"), "text/html")},
        headers=auth,
    )
    result = res.json()
    assert result["failed"] == 0 and result["success"] >= 2, result
    res = client.get("/api/bookmarks", params={"archived": "1"}, headers=auth)
    assert any(b["url"] == "https://example.org/b" for b in res.json()["bookmarks"])


def test_must_change_guard_blocks_business(client):
    # put the account back into the forced-change state, like a fresh install
    conn = sqlite3.connect(os.environ["BOOKMARK_DB_PATH"])
    conn.execute("UPDATE users SET must_change_password = 1 WHERE username = 'admin'")
    conn.commit()
    conn.close()
    data = do_login(client)
    assert data["must_change_password"] is True
    h = {"Authorization": f"Bearer {data['token']}"}
    # business endpoints are refused before the initial password is changed
    assert client.get("/api/bookmarks", headers=h).status_code == 403
    assert client.post(
        "/api/bookmarks", json={"url": "https://example.com/guard", "title": "x"}, headers=h
    ).status_code == 403
    # account info and logout stay reachable; logout kills the token
    assert client.get("/api/me", headers=h).status_code == 200
    assert client.post("/api/logout", headers=h).status_code == 200
    # change password works with a fresh login, and kills the old token
    data = do_login(client)
    h = {"Authorization": f"Bearer {data['token']}"}
    res = client.post(
        "/api/change-password",
        json={"old_password": "admin123", "new_password": "guardpass1"},
        headers=h,
    )
    assert res.status_code == 200
    assert client.get("/api/me", headers=h).status_code == 401
    data2 = do_login(client, "guardpass1")
    assert data2["must_change_password"] is False
    h2 = {"Authorization": f"Bearer {data2['token']}"}
    assert client.get("/api/bookmarks", headers=h2).status_code == 200
    # restore the password so nothing else is affected
    res = client.post(
        "/api/change-password",
        json={"old_password": "guardpass1", "new_password": "admin123"},
        headers=h2,
    )
    assert res.status_code == 200


def test_import_updates_existing_and_search_notes(client, auth):
    html = (
        "<!DOCTYPE NETSCAPE-Bookmark-file-1><DL><p>"
        '<DT><A HREF="https://example.com/manual" ADD_DATE="1700000000" TAGS="upd">第二版标题</A>'
        "<DD>第二版描述[linkding-notes]第二版备注[/linkding-notes]"
        "</DL><p>"
    )
    res = client.post(
        "/api/import",
        files={"file": ("u.html", html.encode("utf-8"), "text/html")},
        headers=auth,
    )
    result = res.json()
    assert result["success"] == 1 and result["failed"] == 0, result
    res = client.get("/api/bookmarks", params={"q": "第二版"}, headers=auth)
    bms = res.json()["bookmarks"]
    assert len(bms) == 1 and bms[0]["title"] == "第二版标题"
    # description-only and notes-only keywords are searchable
    assert client.get("/api/bookmarks", params={"q": "第二版描述"}, headers=auth).json()["total"] == 1
    assert client.get("/api/bookmarks", params={"q": "第二版备注"}, headers=auth).json()["total"] == 1
