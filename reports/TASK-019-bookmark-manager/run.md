# TASK-019 bookmark-manager 执行记录

开工时间：2026-10-21。工作目录：`E:\muse-bridge\in\TASK-019-bookmark-manager`。先读仓库再装依赖、跑测试、起服务。

## 环境

命令：

```
python --version
git -C E:\muse-bridge\in\TASK-019-bookmark-manager status --porcelain
git -C E:\muse-bridge\in\TASK-019-bookmark-manager rev-parse --abbrev-ref HEAD
git -C E:\muse-bridge\in\TASK-019-bookmark-manager log -1 --oneline
```

输出：

```
Python 3.11.9
（porcelain 为空，工作区干净）
main
30c83c2 docs(bookmark-manager): 新增 DECISIONS.md 记录改密口径决定
```

虚拟环境不放进仓库（仓库无 .gitignore，且本任务禁止 rm/del，避免留下删不掉的 .venv）。改放到工作目录。

命令：

```
python -m venv E:\muse-bridge\work\TASK-019-bookmark-manager\.venv
```

输出：exit 0。

## 安装依赖

命令（运行时依赖）：

```
E:\muse-bridge\work\TASK-019-bookmark-manager\.venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-019-bookmark-manager\requirements.txt
```

输出摘要（exit 0）：

```
Successfully installed ... fastapi-0.156.4 ... python-multipart-0.0.32 ... uvicorn-0.54.0
```

命令（测试依赖，按 README 的 requirements-dev.txt，含 httpx / httpx2 / pytest）：

```
E:\muse-bridge\work\TASK-019-bookmark-manager\.venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-019-bookmark-manager\requirements-dev.txt
```

输出摘要（exit 0）：

```
Successfully installed ... httpx-0.28.1 httpx2-2.16.0 ... pytest-9.1.1
```

`pip show httpx2`：Name httpx2，Version 2.16.0，Summary "The next generation HTTP client."，Author-email Tom Christie。仓库源码未 import httpx2（仅 requirements-dev.txt:3）。

## 全量测试（修复前）

工作目录：`E:\muse-bridge\in\TASK-019-bookmark-manager`。

命令：

```
E:\muse-bridge\work\TASK-019-bookmark-manager\.venv\Scripts\python.exe -m pytest tests/ -q
```

输出：

```
.............................                                            [100%]
29 passed in 16.84s
```

exit 0。与 README「共 29 项」一致。

## 起服务（默认端口 8000）

数据库放到工作目录，避免在仓库里生成 `data/bookmarks.db`（任务禁止 rm/del，不能事后删）。启动器：`E:\muse-bridge\work\TASK-019-bookmark-manager\start_server.py`，等价于设置 `BOOKMARK_DB_PATH` 与 `BM_HOST=127.0.0.1` 后执行 `app.py`（未设置 PORT，代码默认 8000）。

命令：

```
E:\muse-bridge\work\TASK-019-bookmark-manager\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-019-bookmark-manager\start_server.py 8000 run-8000.db
```

输出：

```
INFO:     Started server process [26272]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

探测命令：

```
E:\muse-bridge\work\TASK-019-bookmark-manager\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-019-bookmark-manager\probe_http.py http://127.0.0.1:8000 / /health
```

输出：

```
URL http://127.0.0.1:8000/
STATUS 200
CONTENT_TYPE text/html; charset=utf-8
BODY_START
<!DOCTYPE html>
<html lang="zh-CN">
...
<title>书签管理器 · bookmark-manager</title>
BODY_END
URL http://127.0.0.1:8000/health
STATUS 200
CONTENT_TYPE application/json
BODY_START
{"ok":true,"app":"bookmark-manager"}
BODY_END
PROBE_OK
```

随后停掉该进程（kill 后台任务，未使用 taskkill）。

本机 `localhost` 解析（`resolve_host.py`）先是 `127.0.0.1`，再是 `::1`。服务只绑 IPv4 时，另一次探测（服务仍在 8000）：

```
TCP 127.0.0.1:8000 CONNECTED
TCP ::1:8000 FAIL ConnectionRefusedError: [WinError 10061] 由于目标计算机积极拒绝，无法连接。
HTTP http://127.0.0.1:8000/health STATUS 200 BODY b'{"ok":true,"app":"bookmark-manager"}'
HTTP http://localhost:8000/health STATUS 200 BODY b'{"ok":true,"app":"bookmark-manager"}'
HTTP http://[::1]:8000/health FAIL TimeoutError: timed out
```

urllib 打开 README 写的 `localhost:8000` 得到 200。直接连 `::1` 被拒绝。没有浏览器工具，没有把「浏览器打不开」记成已复现。

## 真实数据自测（8123，新库）

先停 8000，再用新库起 8123。

命令：

```
E:\muse-bridge\work\TASK-019-bookmark-manager\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-019-bookmark-manager\start_server.py 8123 run-8123.db
```

输出：

```
INFO:     Started server process [22056]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8123 (Press CTRL+C to quit)
```

自测命令（`run_live.py` 设置 `BASE=http://127.0.0.1:8123` 后执行 `tests/live_selftest.py`）：

```
E:\muse-bridge\work\TASK-019-bookmark-manager\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-019-bookmark-manager\run_live.py
```

输出（exit 0）：

```
✓ 登录成功，首次登录需改密标记 = True
✓ 改密成功
✓ 改密后旧 token 失效，重新登录拿到新 token
✓ 导入真实书签：{'total': 9, 'success': 9, 'failed': 0, 'skipped': 0, 'dropped_tags': []}
✓ 列表（默认不含归档）共 8 条
✓ 归档区有 1 条（Linkding 官网），伪标签已还原成归档状态
✓ 给 Hacker News 补标签：['技术', '每天看', '资讯']
✓ 按新标签筛选命中 1 条
✓ 搜索“文档”命中 3 条
✓ 导出成功，文件 1510 字节，含归档伪标签
✓ 真实外网抓取 docs.python.org：status=200 title='3.15.0 Documentation'
LIVE SELFTEST PASSED
```

外网抓取这一步成功，未标成环境限制，也没有重试。

## 关闭服务

8123 与后来再次拉起的 8000 都已停掉（kill 后台任务，未使用 taskkill）。停完后探测 8000：

```
TCP 127.0.0.1:8000 FAIL ConnectionRefusedError: [WinError 10061] 由于目标计算机积极拒绝，无法连接。
HTTP http://127.0.0.1:8000/health FAIL URLError: <urlopen error [WinError 10061] 由于目标计算机积极拒绝，无法连接。>
HTTP http://localhost:8000/health FAIL URLError: <urlopen error [WinError 10061] 由于目标计算机积极拒绝，无法连接。>
```

修复前 `git status --porcelain` 为空。

## 修复 P0-1 之后的全量测试

只改了 `static/index.html` 一处：`loadAll()` → `refresh()`。

命令：

```
E:\muse-bridge\work\TASK-019-bookmark-manager\.venv\Scripts\python.exe -m pytest tests/ -q
```

输出（exit 0）：

```
.............................                                            [100%]
29 passed in 15.94s
```




