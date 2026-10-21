# bookmark-manager 修复记录

只改 review.md 清单里的 P1-1、P1-2。P1-3 不改，原因见文末。测试文件未改。

## P1-1 数据接口在未改密时拒绝

问题：`must_change_password` 只影响前端。审查时 `current_user`（当时 app.py:211-227）不看这个标志，未改密也能调用书签接口。

文件：`app.py`。新增 `require_changed_password`（现 app.py:230-234）。下列数据接口的依赖从 `current_user` 改为 `require_changed_password`（行号为改后）：app.py:402、475、517、560、569、608、621、781、828。`/api/login`、`/api/me`（app.py:294）、`/api/change-password`（app.py:275）、`/api/logout`（app.py:263）仍只用 `current_user`。

改法：已登录但 `must_change_password` 为真时，数据接口返回 403，`detail` 为「请先修改密码」。

验证命令：

```
Set-Location E:\muse-bridge\in\TASK-012-bookmark-manager
E:\muse-bridge\work\TASK-012-bookmark-manager\.venv\Scripts\python.exe -m pytest tests/ -q --tb=short
E:\muse-bridge\work\TASK-012-bookmark-manager\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-012-bookmark-manager\probe_p11.py
```

pytest 输出：

```
21 passed, 3 warnings in 4.29s
```

退出码 0。警告仍是 `on_event` 弃用和 Starlette/httpx TestClient 弃用，与改前相同。

probe_p11.py 输出：

```
LOGIN 200 {"token":"...","username":"admin","must_change_password":true}
BOOKMARKS_BEFORE 403 {"detail":"请先修改密码"}
ME_BEFORE 200 {"username":"admin","must_change_password":true}
LOGOUT 200 {"ok":true}
CHANGE 200 {"ok":true}
BOOKMARKS_AFTER 200 {"bookmarks":[],"total":0}
NOAUTH 401
```

未改密时列表 403；`/api/me` 与退出仍可用；改密后列表 200；无 token 仍是 401。

中途核对时，`app.py` 和 `README.md` 一度回到修改前的内容（`git diff` 为空）。已按同一改法重新写入。下面的 pytest、403 探测和 8000 绑定检查都是重新写入之后跑的。当前 `git status --short` 只有 `M README.md` 和 `M app.py`。

## P1-2 默认只监听本机

问题：审查时 app.py:847 为 `host="0.0.0.0"`。启动日志曾是 `Uvicorn running on http://0.0.0.0:8000`。登录页仍含默认口令（static/index.html:66），这次没改那句。

文件：`app.py:854-858`，`README.md:50`。

改法：`host=os.environ.get("HOST", "127.0.0.1")`。README 环境变量表增加 `HOST`，默认 `127.0.0.1`。

验证命令（重新写入之后）：

```
E:\muse-bridge\work\TASK-012-bookmark-manager\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-012-bookmark-manager\run_bind8000.py
```

输出片段：

```
SRC 856:        host=os.environ.get("HOST", "127.0.0.1"),
CHILD_HOST None
PID 19964
HEALTH 200 {"ok":true,"app":"bookmark-manager"}
HOME 200 <!DOCTYPE html>
NETSTAT
  TCP    127.0.0.1:8000         0.0.0.0:0              LISTENING       28428
INFO:     Started server process [28428]
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:62108 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:56470 - "GET / HTTP/1.1" 200 OK
```

脚本随后 `terminate()`。退出码 1 是进程被终止，不是启动失败。事后 `netstat` 已无 `:8000` 的 LISTENING。

同一版改动在被还原之前还测过：不设 `HOST`、`PORT=8123` 时日志为 `Uvicorn running on http://127.0.0.1:8123`；`HOST=0.0.0.0`、`PORT=8001` 时为 `Uvicorn running on http://0.0.0.0:8001`，`/health` 200。那次 `tests/live_selftest.py` 退出码 0，末行 `LIVE SELFTEST PASSED`。外网标题这次是 `title=None`（第一次审查时是 `'3.15.0 Documentation'`）。自测脚本不因标题为空而失败，记为环境波动，没有再重试。

## P1-3 改密不撤销其他会话

未改。`change_password` 仍只更新 `users`（现 app.py:275 起）。原因：`tests/test_app.py:31-34` 的模块级 token 在 `test_change_password`（test_app.py:55-70）里先改密，再用另一个 token 把密码改回；第二次若删除其他会话，后面的用例会 401。测试文件不许改。

## 全量测试

两处修改都落在当前文件上之后执行：

```
Set-Location E:\muse-bridge\in\TASK-012-bookmark-manager
E:\muse-bridge\work\TASK-012-bookmark-manager\.venv\Scripts\python.exe -m pytest tests/ -q --tb=line
```

输出：

```
21 passed, 3 warnings in 4.18s
```

退出码 0。没有失败项。3 条警告与改前相同：`app.py:192` 的 `on_event` 弃用，以及 Starlette 关于 httpx TestClient 的弃用。未改测试，未改依赖版本，未改 LICENSE / UPSTREAM。
