"""Live end-to-end self-test against a real running server with real data.
Not a pytest module. Run: .venv/bin/python tests/live_selftest.py
Assumes the server is already running on $BASE (default http://127.0.0.1:8123)
with a fresh database (initial admin/admin123).
"""
import json
import os
import urllib.parse
import urllib.request

BASE = os.environ.get("BASE", "http://127.0.0.1:8123")

REAL_BOOKMARKS = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><H3>开发文档</H3>
    <DL><p>
        <DT><A HREF="https://docs.python.org/3/" ADD_DATE="1729000000" TAGS="python,文档">Python 官方文档</A>
        <DD>Python 3 文档首页
        <DT><A HREF="https://developer.mozilla.org/zh-CN/" ADD_DATE="1729000100" TAGS="文档,前端">MDN Web Docs</A>
        <DT><A HREF="https://fastapi.tiangolo.com/zh/" ADD_DATE="1729000200" TAGS="python,fastapi">FastAPI 中文文档</A>
    </DL><p>
    <DT><H3>工具</H3>
    <DL><p>
        <DT><A HREF="https://github.com/" ADD_DATE="1729000300" TAGS="工具,代码托管" TOREAD="1">GitHub</A>
        <DT><A HREF="https://stackoverflow.com/" ADD_DATE="1729000400" TAGS="工具,问答">Stack Overflow</A>
        <DT><A HREF="https://www.wikipedia.org/" ADD_DATE="1729000500" TAGS="工具,百科">维基百科</A>
    </DL><p>
    <DT><A HREF="https://news.ycombinator.com/" ADD_DATE="1729000600" TAGS="资讯,技术">Hacker News</A>
    <DT><A HREF="https://www.runoob.com/" ADD_DATE="1729000700" TAGS="教程,编程">菜鸟教程</A>
    <DT><A HREF="https://linkding.link/" ADD_DATE="1729000800" TAGS="linkding:bookmarks.archived,开源">Linkding 官网</A>
</DL><p>
"""


def call(method, path, token=None, body=None, raw=None, ctype="application/json"):
    data = raw
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    if data is not None:
        headers["Content-Type"] = ctype
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def main():
    steps = []

    status, text = call("POST", "/api/login", body={"username": "admin", "password": "admin123"})
    assert status == 200, text
    login = json.loads(text)
    token = login["token"]
    steps.append(f"登录成功，首次登录需改密标记 = {login['must_change_password']}")

    status, text = call("POST", "/api/change-password", token,
                        body={"old_password": "admin123", "new_password": "selftest-pass-1"})
    assert status == 200, text
    steps.append("改密成功")
    # password change drops all sessions: the initial token is dead, log in again
    status, text = call("POST", "/api/login", body={"username": "admin", "password": "selftest-pass-1"})
    assert status == 200, text
    token = json.loads(text)["token"]
    steps.append("改密后旧 token 失效，重新登录拿到新 token")

    # import via multipart
    boundary = "----bm-boundary"
    raw = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="file"; filename="bookmarks.html"\r\n'
        "Content-Type: text/html\r\n\r\n"
    ).encode() + REAL_BOOKMARKS.encode("utf-8") + f"\r\n--{boundary}--\r\n".encode()
    status, text = call("POST", "/api/import", token, raw=raw,
                        ctype=f"multipart/form-data; boundary={boundary}")
    assert status == 200, text
    result = json.loads(text)
    steps.append(f"导入真实书签：{result}")
    assert result == {"total": 9, "success": 9, "failed": 0}, result

    status, text = call("GET", "/api/bookmarks", token)
    data = json.loads(text)
    assert data["total"] == 8, data  # 9 imported minus 1 archived
    steps.append(f"列表（默认不含归档）共 {data['total']} 条")

    status, text = call("GET", "/api/bookmarks?archived=1", token)
    arch = json.loads(text)["bookmarks"]
    assert len(arch) == 1 and arch[0]["title"] == "Linkding 官网", arch
    steps.append("归档区有 1 条（Linkding 官网），伪标签已还原成归档状态")

    # tag an existing bookmark through the edit API
    status, text = call("GET", "/api/bookmarks?q=Hacker", token)
    hn = json.loads(text)["bookmarks"][0]
    status, text = call("PUT", f"/api/bookmarks/{hn['id']}", token,
                        body={"tags": "资讯, 技术, 每天看"})
    assert status == 200, text
    steps.append(f"给 Hacker News 补标签：{json.loads(text)['tags']}")

    status, text = call("GET", "/api/bookmarks?tag=" + urllib.parse.quote("每天看"), token)
    assert json.loads(text)["total"] == 1
    steps.append("按新标签筛选命中 1 条")

    status, text = call("GET", "/api/bookmarks?q=" + urllib.parse.quote("文档"), token)
    hits = json.loads(text)["total"]
    assert hits >= 3, hits
    steps.append(f"搜索“文档”命中 {hits} 条")

    status, text = call("GET", "/api/export", token)
    assert status == 200 and "docs.python.org" in text and "linkding:bookmarks.archived" in text
    steps.append(f"导出成功，文件 {len(text)} 字节，含归档伪标签")

    # real external scrape attempt (cloud egress may or may not cooperate)
    status, text = call("POST", "/api/fetch-metadata", token,
                        body={"url": "https://docs.python.org/3/"})
    meta = json.loads(text) if status == 200 else {}
    steps.append(f"真实外网抓取 docs.python.org：status={status} title={meta.get('title')!r}")

    print("\n".join("✓ " + s for s in steps))
    print("LIVE SELFTEST PASSED")


if __name__ == "__main__":
    main()
