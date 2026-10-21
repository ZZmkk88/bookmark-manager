# TASK-012-bookmark-manager 执行记录

开工时间：2026-10-21。工作目录：`E:\muse-bridge\in\TASK-012-bookmark-manager`。先审查再按清单修 P0/P1。

## 步骤 1：确认 Python

命令：

```
python --version
py -3 --version
```

输出：

```
Python 3.11.9
Unable to create process using 'E:\python.exe --version': ???????????
```

退出码：`python --version` 成功（3.11.9，满足 README 要求的 3.10+）。`py -3` 启动器指向无效的 `E:\python.exe`，后续一律用 `python`。

## 步骤 2：创建虚拟环境（放在 work 目录，不写进仓库）

命令（虚拟环境放在 work 目录，避免写入仓库）：

```
python -m venv E:\muse-bridge\work\TASK-012-bookmark-manager\.venv
Set-Location E:\muse-bridge\in\TASK-012-bookmark-manager
E:\muse-bridge\work\TASK-012-bookmark-manager\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

结果：venv 创建成功（退出码 0）。pip 退出码 0。装上的版本与 requirements 一致：fastapi 0.156.4、uvicorn 0.54.0、python-multipart 0.0.32、httpx 0.28.1、pytest 9.1.1。传递依赖含 starlette 1.9.0、pydantic 2.14.1。无依赖冲突。

## 步骤 3：按 README 跑 pytest

命令（在仓库根目录，解释器为 work 下的 venv；与 README 的 `.venv\Scripts\python -m pytest tests/ -q` 等价，只是 venv 不在仓库内）：

```
Set-Location E:\muse-bridge\in\TASK-012-bookmark-manager
E:\muse-bridge\work\TASK-012-bookmark-manager\.venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

输出：

```
.....................                                                    [100%]
============================== warnings summary ===============================
app.py:192
  DeprecationWarning: on_event is deprecated, use lifespan event handlers instead.
    @app.on_event("startup")
fastapi\testclient.py:1
  StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
21 passed, 3 warnings in 4.37s
```

退出码 0。21 项全部通过，与 README「共 21 项」一致。3 条是弃用警告，不是失败。

说明：`tests/test_app.py` 第 10 行使用 `tempfile.mkdtemp`，临时库落在进程 TEMP。尝试用 `$env:TEMP` 改到 work 目录时，该命令被本机会话策略拦住（含 `$env:`），因此这次 pytest 未改 TEMP。后续自建库会显式放到 work 目录。

## 步骤 4：起服务，检查首页和 /health

按 README 默认端口 8000 启动。数据库放到 work 目录，避免在仓库里生成 `data/bookmarks.db`。入口仍是仓库里的 `app.py`。未使用 curl/wget。

### 4a. 第一次后台启动（中途进程自己退出）

命令：

```
E:\muse-bridge\work\TASK-012-bookmark-manager\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-012-bookmark-manager\start_server.py default
```

`start_server.py` 会设置 `BOOKMARK_DB_PATH` 到 work 目录、去掉 `PORT`，再用 `runpy` 以 `__main__` 执行仓库 `app.py`。

已看到的日志：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:60754 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:60755 - "GET / HTTP/1.1" 200 OK
```

当时用 `http_check.py` 取到：`/health` 为 `{"ok":true,"app":"bookmark-manager"}`，首页 HTTP 200 且正文以 `<!DOCTYPE html>` 开头。随后该后台进程退出，退出码 1，日志没有 traceback。日志里还多了本会话没有发的请求：`GET /api/health` 404、`GET /docs` 200、`GET /api/me` 401。不把这次退出当成应用崩溃结论，下面用前台监督脚本重跑。

### 4b. 监督脚本：默认端口 + 行为探测 + 8123 全流程自测，然后关掉

命令：

```
E:\muse-bridge\work\TASK-012-bookmark-manager\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-012-bookmark-manager\run_flow.py
```

脚本做的事：子进程运行仓库 `app.py`（venv 解释器，cwd 为仓库）。第一次不设 `PORT`，`BOOKMARK_DB_PATH=E:\muse-bridge\work\TASK-012-bookmark-manager\default-8000.db`。检查完后 `terminate`。第二次 `PORT=8123`，`BOOKMARK_DB_PATH=...\live-8123.db`，再跑 `tests\live_selftest.py`（`BASE=http://127.0.0.1:8123`），然后 `terminate`。

输出片段（退出码 0，完整输出在 `E:\muse-bridge\work\TASK-012-bookmark-manager\flow-output.txt`）：

```
HEALTH 200 {"ok":true,"app":"bookmark-manager"}
HOME 200 title_ok=True has_admin123=True bytes=15183
DOCS 200 len=1015
LOGIN 200 {"token":"...","username":"admin","must_change_password":true}
BOOKMARKS_BEFORE_PWCHANGE 200 {"bookmarks":[],"total":0}
CREATE_LONG_TAG 201 {..."tags":["ok-tag"]}
SEARCH_NOTES 200 {..."total":1}
PWCHANGE 200 {"ok":true}
TOKEN_B_AFTER_PWCHANGE 200 {"username":"admin","must_change_password":false}
TOKEN_A_AFTER_PWCHANGE 200 {"username":"admin","must_change_password":false}
SEARCH_QUOTE 200 {"bookmarks":[],"total":0}
```

服务日志：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Uvicorn running on http://0.0.0.0:8123 (Press CTRL+C to quit)
```

`live_selftest.py` 退出码 0，耗时 8.86 秒：

```
✓ 登录成功，首次登录需改密标记 = True
✓ 改密成功
✓ 导入真实书签：{'total': 9, 'success': 9, 'failed': 0}
✓ 列表（默认不含归档）共 8 条
✓ 归档区有 1 条（Linkding 官网），伪标签已还原成归档状态
✓ 给 Hacker News 补标签：['技术', '每天看', '资讯']
✓ 按新标签筛选命中 1 条
✓ 搜索“文档”命中 3 条
✓ 导出成功，文件 1510 字节，含归档伪标签
✓ 真实外网抓取 docs.python.org：status=200 title='3.15.0 Documentation'
LIVE SELFTEST PASSED
```

外网抓标题这一次就成功了，不标环境限制，也没有重试。

两个服务进程的 returncode 都是 1：这是监督脚本调用 `terminate()` 关掉它们的结果（Windows 上被终止的进程常为 1）。日志停在最后一次 HTTP 200，没有异常栈。端口已释放。仓库内没有生成 `data/bookmarks.db`。

## 步骤 5：写审查结论

见 `E:\muse-bridge\out\TASK-012-bookmark-manager\review.md`。修复放在该文件清单之后，不在本步骤改仓库源码。
