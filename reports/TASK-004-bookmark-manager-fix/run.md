# TASK-004 执行记录

开工：2026-10-21。工作目录 `E:\muse-bridge\in\TASK-004-bookmark-manager-fix`。先读代码与上一轮问题定位，再逐条修改并验证。

## 严重1 未改密拦截 + 改密作废会话

改 `app.py` 的 `current_user` / `change_password`，`static/index.html` 改密成功后写回新 token，`tests/test_app.py` 增加对应用例。

命令（工作目录即仓库）：

```text
E:\muse-bridge\env\bookmark-manager\Scripts\python.exe -m pytest tests/test_app.py -k "test_login_ok_and_must_change or test_must_change_blocks_business_api or test_change_password" -q --tb=short
```

退出码 0。

```text
3 passed, 19 deselected, 3 warnings in 1.63s
```

此时 `app.py:192` 的 `@app.on_event("startup")` 弃用警告还在（一般项 7 尚未改）。

## 其余代码改完后的全量 pytest

已改：lifespan、关闭 `/docs`、LIKE 转义、`HOST` 默认 `127.0.0.1`，以及 README / NOTES / LICENSE。

命令：

```text
E:\muse-bridge\env\bookmark-manager\Scripts\python.exe -m pytest -q --tb=short
```

退出码 0。

```text
.........................                                                [100%]
============================== warnings summary ===============================
..\..\env\bookmark-manager\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\env\bookmark-manager\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
25 passed, 1 warning in 4.62s
```

`on_event` 弃用警告已消失。剩下的 1 条来自当前环境的 Starlette TestClient（`fastapi/testclient.py` 引入 `starlette.testclient`，并提示改用 httpx2）。

## 短时启动（默认 HOST、随机端口）

命令：

```text
E:\muse-bridge\env\bookmark-manager\Scripts\python.exe E:\muse-bridge\work\TASK-004-bookmark-manager-fix\bindcheck.py
```

数据库：`E:\muse-bridge\work\TASK-004-bookmark-manager-fix\bindcheck.db`。环境里去掉 `HOST`，只设置 `PORT` 为临时端口。退出码 0。耗时未另用计时器；进程在同一条命令里启动并 `terminate`。

```text
PORT 62755
PID 26436
HEALTH 200 {"ok":true,"app":"bookmark-manager"}
DOCS 404
REDOC 404
OPENAPI 404
LOGIN 200 {"token":"<43字符，记录里抹掉>","username":"admin","must_change_password":true}
LIST 403 {"detail":"请先修改密码"}
ME 200 {"username":"admin","must_change_password":true}
LISTENERS
TCP    127.0.0.1:62755        0.0.0.0:0              LISTENING       25836
STOPPED 1
AFTER_STOP ConnectTimeout: timed out
INFO:     Started server process [25836]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:62755 (Press CTRL+C to quit)
INFO:     127.0.0.1:57700 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:51737 - "GET /docs HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:49320 - "GET /redoc HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:53137 - "GET /openapi.json HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:53138 - "POST /api/login HTTP/1.1" 200 OK
INFO:     127.0.0.1:49501 - "GET /api/bookmarks HTTP/1.1" 403 Forbidden
INFO:     127.0.0.1:49504 - "GET /api/me HTTP/1.1" 200 OK
```

停掉之后再查端口（`netstat -ano | findstr 62755`）：只剩客户端 `TIME_WAIT`，没有 `LISTENING`。

## 本机已装版本

命令：

```text
E:\muse-bridge\env\bookmark-manager\Scripts\python.exe -c "import fastapi, uvicorn, httpx, pytest; print('fastapi', fastapi.__version__); print('uvicorn', uvicorn.__version__); print('httpx', httpx.__version__); print('pytest', pytest.__version__)"
```

退出码 0。

```text
fastapi 0.153.0
uvicorn 0.54.0
httpx 0.28.1
pytest 9.1.1
```

## 改动范围

`git diff --stat`（未 commit）：

```text
 LICENSE           |  7 +++++
 NOTES.md          |  2 +-
 README.md         | 11 ++++----
 app.py            | 40 +++++++++++++++++++++++------
 static/index.html |  6 ++++-
 tests/test_app.py | 77 ++++++++++++++++++++++++++++++++++++++++++++++++++++++-
 6 files changed, 127 insertions(+), 16 deletions(-)
```

`tests/live_selftest.py` 第 115–116 行会向 `https://docs.python.org/3/` 抓标题。按禁止外网，没有跑。
