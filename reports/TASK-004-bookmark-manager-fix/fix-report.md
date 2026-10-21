# 修复记录

工作目录 `E:\muse-bridge\in\TASK-004-bookmark-manager-fix`。解释器 `E:\muse-bridge\env\bookmark-manager\Scripts\python.exe`（Python 3.11.9，上一轮审查已记录；本轮未重打 `sys.version`）。

最终全量命令：

```text
E:\muse-bridge\env\bookmark-manager\Scripts\python.exe -m pytest -q --tb=short
```

退出码 0。

```text
25 passed, 1 warning in 4.62s
```

警告只剩环境里的 Starlette TestClient。`@app.on_event("startup")` 的 DeprecationWarning 已不再出现。

## 严重1 未改密可调业务接口，改密不废除旧 token

问题：`current_user` 不看 `must_change_password`；`change_password` 只更新 `users`。

改动：

- `app.py:234-239`：`must_change_password` 为真，且路径不是 `/api/change-password`、`/api/logout`、`/api/me` 时返回 403，`detail` 为「请先修改密码」。
- `app.py:291-302`：更新密码后 `DELETE FROM sessions WHERE user_id = ?`，再 `secrets.token_urlsafe(32)` 插入新会话，`commit` 后返回 `{"ok": true, "token": new_token}`。
- `static/index.html:185-193`：改密响应里有 `data.token` 时写回 `bm_token`，再调用 `boot()`。
- `tests/test_app.py:61-104`：未改密时列表 403、`/api/me` 200、错误旧密码的改密请求为 400；改密后旧 token 访问 `/api/me` 为 401，新 token 可用，并把共享 `auth` 头换成新 token，避免后续用例被作废会话拖垮。

验证：

```text
E:\muse-bridge\env\bookmark-manager\Scripts\python.exe -m pytest tests/test_app.py -k "test_login_ok_and_must_change or test_must_change_blocks_business_api or test_change_password" -q --tb=short
```

退出码 0：`3 passed, 19 deselected, 3 warnings in 1.63s`（当时 lifespan 尚未改，所以仍有 on_event 警告）。

全量 pytest 再次包含这两条，`25 passed`。

短时进程（`bindcheck.py`，端口 62755）：`LIST 403 {"detail":"请先修改密码"}`，`ME 200` 且 `must_change_password` 为 true。

页面脚本没有在浏览器里点过。本环境没有浏览器工具。写回 token 的依据是 `static/index.html:185-193` 的源码。

## 严重2 默认监听 0.0.0.0

问题：`uvicorn.run(..., host="0.0.0.0")`。

改动：

- `app.py:871`：`host=os.environ.get("HOST", "127.0.0.1")`，端口仍用 `PORT`。
- `README.md:47`：环境变量表增加 `HOST`，默认 `127.0.0.1`。

验证：`tests/test_app.py:384` `test_uvicorn_default_host_is_loopback` 在未设置 `HOST` 时断言 `uvicorn.run` 的 `host` 为 `127.0.0.1`，设置 `HOST=0.0.0.0` 时断言为 `0.0.0.0`。包含在 `25 passed` 里。

短时进程未设置 `HOST`。日志：`Uvicorn running on http://127.0.0.1:62755`。`netstat`：`TCP 127.0.0.1:62755 ... LISTENING`（pid 25836）。没有 `0.0.0.0:62755` 的 LISTENING 行。`terminate` 之后 `GET /health` 为 `ConnectTimeout`，再查 `netstat` 只剩 `TIME_WAIT`。

## 严重3 LICENSE 没有上游版权声明

问题：LICENSE 只有本项目 2026 版权行。禁止凭记忆补上游姓名。

改动：`LICENSE:23-28` 末尾增加 NOTICE。写明本作品为独立实现，归档伪标签 `linkding:bookmarks.archived` 与备注标记 `[linkding-notes]` 沿用 Linkding（MIT，`https://github.com/sissbruecker/linkding`）。原文一句：「上游版权行待从 sissbruecker/linkding 的 LICENSE 原样补入」。

验证：改完后读了 `LICENSE:23-28`，`git diff -- LICENSE` 只有这 7 行。没有联网，上游版权人姓名和年份未核实，也没有写进文件。

## 一般4 搜索 LIKE 通配符；「全文搜索」

问题：`LIKE '%关键词%'` 不转义 `%` `_`；README 开篇写全文搜索。

改动：

- `app.py:551-558`：先把 `\`、`%`、`_` 转义，五个 `LIKE` 都带 `ESCAPE '\'`。
- `README.md:4`：「全文搜索」改为「关键词搜索」。

验证：`tests/test_app.py:190` `test_search_escapes_like_wildcards`。`q=%` 只命中标题 `100%done`；`q=e%d` 为 0；`keep_underscore` 为 1；`keepXunderscore` 为 0；反斜杠备注可被字面量命中。包含在 `25 passed` 里。

## 一般5 文档写死 localhost:8000

问题：README 让人打开 `http://localhost:8000`，并只提到端口 8000。

改动：

- `README.md:38`：注释改为默认 `127.0.0.1:8000`，可用 `HOST`、`PORT` 改。
- `README.md:41`：改为打开 `http://<HOST>:<PORT>`，未设置时是 `http://127.0.0.1:8000`。

验证：`git diff -- README.md` 中这两行与上面一致。监听行为见严重2。

## 一般6 未登录可打开 /docs

问题：FastAPI 默认文档未鉴权即 200。

改动：`app.py:197-203` 的 `FastAPI(...)` 设置 `docs_url=None, redoc_url=None, openapi_url=None`。

验证：`tests/test_app.py:55` `test_docs_not_public` 断言这三条路径都不是 200。包含在 `25 passed` 里。

短时进程：`DOCS 404`、`REDOC 404`、`OPENAPI 404`。日志分别是 `404 Not Found`。

## 一般7 startup 事件弃用

问题：`@app.on_event("startup")` 触发 DeprecationWarning。

改动：删掉该装饰器。`app.py:191-203` 改为 `lifespan`：进入时调用 `init_db()`，再 `yield`。`app = FastAPI(...)` 挪到 `init_db` 之后、第一个路由之前。`login` 里的 `init_db()` 仍保留。

验证：全量 pytest 的 warnings summary 里没有 `on_event`。只剩：

```text
fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
25 passed, 1 warning in 4.62s
```

## 一般8 导入统计没写文件内重复

问题：README 只写「已存在则更新」，没写同一文件里后出现的重复归一化网址。

改动：`README.md:27` 补上「同一文件内重复的归一化网址计为 failed，不覆盖先出现的那条」。导入代码未改。

验证：`git diff -- README.md` 含这一句。原有 `test_import_netscape` 仍要求样例文件 `{"total": 4, "success": 2, "failed": 2}`，包含在 `25 passed` 里。

## 一般9 NOTES 版本号与本机 venv 不一致

问题：NOTES 写 fastapi `0.156.4`。

改动：`NOTES.md:6` 改为「依赖见 requirements.txt」。没有把本机版本写进 NOTES。

验证：本机实测（退出码 0）：

```text
fastapi 0.153.0
uvicorn 0.54.0
httpx 0.28.1
pytest 9.1.1
```

`0.156.4` 已从 NOTES 删掉。`requirements.txt` 仍是 `fastapi>=0.110` 等下限，没有写死补丁号。

## 附带

`README.md:56` 的测试条数从 21 改为 25，与本轮新增用例一致（原 21 项都还在：`25 passed` 含原有用例名）。

未改、也不在本轮清单里的包括：与 Linkding / 浏览器互通的措辞、有标题时不抓描述、搜索框占位文案、只写 Unix 的运行说明、测试共用模块级数据库。
