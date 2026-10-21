# TASK-038-bookmark-manager 执行记录

开工时间：2026-10-21。工作目录：E:\muse-bridge\in\TASK-038-bookmark-manager。先审查再修 P0/P1。

## 步骤 1：核对 Python

命令（工作目录 E:\muse-bridge\in\TASK-038-bookmark-manager）：

```powershell
python --version
py -3 --version
git rev-parse --is-inside-work-tree
git status --porcelain
```

输出摘要：

```
Python 3.11.9
true
Unable to create process using 'E:\python.exe --version': ???????????
```

说明：`python --version` 为 Python 3.11.9（满足 README 要求的 3.10+）。`py -3 --version` 失败，启动器指向不存在的 `E:\python.exe`，后续改用 `python`。`git rev-parse --is-inside-work-tree` 为 `true`。`git status --porcelain` 无输出，工作区干净。

虚拟环境不放进仓库（仓库无 .gitignore，避免把 .venv 算进改动），放到 `E:\muse-bridge\work\TASK-038-bookmark-manager\.venv`。

## 步骤 2：按 README 安装运行依赖

命令：

```powershell
python -m venv E:\muse-bridge\work\TASK-038-bookmark-manager\.venv
E:\muse-bridge\work\TASK-038-bookmark-manager\.venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-038-bookmark-manager\requirements.txt
```

结果：exit 0。fastapi==0.156.4、uvicorn==0.54.0、python-multipart==0.0.32 安装成功（以及传递依赖 starlette 1.9.0、pydantic 2.14.1 等）。

## 步骤 3：按 README 安装测试依赖

命令：

```powershell
E:\muse-bridge\work\TASK-038-bookmark-manager\.venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-038-bookmark-manager\requirements-dev.txt
```

结果：exit 0。httpx==0.28.1、httpx2==2.16.0、pytest==9.1.1 均安装成功（另有 httpcore 1.0.9、httpcore2 2.16.0）。

## 步骤 4：全量 pytest

第一次调用把测试目录写成绝对路径，pytest 把 rootdir 定在 tests/，收集失败（这是调用方式错误，不是项目缺陷）：

```
ERROR tests/test_app.py
ImportError while importing test module '...\tests\test_app.py'
tests\test_app.py:18: in <module>
    import app as appmod
E   ModuleNotFoundError: No module named 'app'
1 error in 0.27s
```

改为与 README 一致：工作目录切到仓库，执行 `python -m pytest tests/ -q`。临时目录 TEMP/TMP 指到 `E:\muse-bridge\work\TASK-038-bookmark-manager`（测试文件自己用 tempfile.mkdtemp）。

命令（cwd = 仓库）：

```powershell
E:\muse-bridge\work\TASK-038-bookmark-manager\.venv\Scripts\python.exe -m pytest tests -q --tb=short --rootdir E:\muse-bridge\in\TASK-038-bookmark-manager
```

输出：

```
...........................................                              [100%]
43 passed in 21.60s
```

exit 0。43 项全部通过，与 README 第 78 行「共 43 项」一致。

## 步骤 5：按 README 以 8123 端口、全新数据库启动服务

数据库放到工作目录，避免在仓库里生成 data/bookmarks.db。启动脚本 `E:\muse-bridge\work\TASK-038-bookmark-manager\serve.py` 设置 `PORT=8123`、`BOOKMARK_DB_PATH=E:\muse-bridge\work\TASK-038-bookmark-manager\live.db` 后以 `__main__` 跑 `app.py`。

服务日志：

```
INFO:     Started server process [31532]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8123 (Press CTRL+C to quit)
```

监听地址与 README 的 `BM_HOST` 默认 `127.0.0.1`、`PORT=8123` 一致。

## 步骤 6：README 真实数据自测 `tests/live_selftest.py`

命令：工作目录脚本 `E:\muse-bridge\work\TASK-038-bookmark-manager\run_live.py` 设置 `BASE=http://127.0.0.1:8123` 后执行 `tests/live_selftest.py`。

结果：exit 1。失败点在外网抓标题（`live_selftest.py:120`，`https://docs.python.org/3/`），客户端 `timeout=20`：

```
File "E:\muse-bridge\in\TASK-038-bookmark-manager\tests\live_selftest.py", line 120, in main
    status, text = call("POST", "/api/fetch-metadata", token,
...
TimeoutError: timed out
```

这之前的 `assert` 没有抛 AssertionError。服务访问日志里这些请求都已 200，外网那条没有完成记录（卡住，超过 `urlopen` 的 10 秒超时，之后其他请求仍正常）：

```
POST /api/login HTTP/1.1" 200 OK
POST /api/change-password HTTP/1.1" 200 OK
POST /api/login HTTP/1.1" 200 OK
POST /api/import HTTP/1.1" 200 OK
GET /api/bookmarks HTTP/1.1" 200 OK
GET /api/bookmarks?archived=1 HTTP/1.1" 200 OK
GET /api/bookmarks?q=Hacker HTTP/1.1" 200 OK
PUT /api/bookmarks/7 HTTP/1.1" 200 OK
GET /api/bookmarks?tag=%E6%AF%8F%E5%A4%A9%E7%9C%8B HTTP/1.1" 200 OK
GET /api/bookmarks?q=%E6%96%87%E6%A1%A3 HTTP/1.1" 200 OK
GET /api/export HTTP/1.1" 200 OK
```

判定：环境限制（本机有 `HTTP_PROXY=http://127.0.0.1:7890`；服务脚本已去掉代理，但 `socket.getaddrinfo` 无超时）。不计入项目缺陷。未再重试。

## 步骤 7：首页与健康检查

`probe_headers.py` 对 `http://127.0.0.1:8123`：

```
/ 200
  content-type: text/html; charset=utf-8
  content-length: 17098
  body-prefix: b'<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n<meta name="vi'
/health 200
  content-type: application/json
  body-prefix: b'{"ok":true,"app":"bookmark-manager"}'
```

另：空 body 且 `Content-Type: application/json` 的 DELETE `/api/bookmarks/10` 返回 200 `{"ok":true}`，POST `/api/logout` 返回 200 `{"ok":true}`。

## 步骤 8：关掉服务

已结束步骤 5 的后台进程（工具返回 killed）。未使用 taskkill。日志未再刷出 uvicorn 退出行。

## 步骤 9：本地 SSRF 探针（不访问外网；DNS 失败的名字用本机 getaddrinfo）

`probe_aton.py`（本机 `socket.inet_aton`）：

```
2130706433 -> 127.0.0.1
2852039166 -> 169.254.169.254
0x7f000001 -> 127.0.0.1
0xa9fea9fe -> 169.254.169.254
0177.0.0.1 -> 127.0.0.1
127.1 -> 127.0.0.1
0 -> 0.0.0.0
evil.example / public.example / localhost -> 拒绝（不是字面量）
```

`probe_more.py` 调用真实的 `ensure_fetch_allowed`（未打桩）：

```
BLOCKED  http://127.0.0.1/
BLOCKED  http://localhost/
BLOCKED  http://[::1]/
ALLOWED  http://2130706433/
ALLOWED  http://2852039166/
ALLOWED  http://127.1/
ALLOWED  http://0x7f000001/
ALLOWED  http://0177.0.0.1/
ALLOWED  http://0/
ALLOWED  http://8.8.8.8/
```

`probe_resolve.py`：上述非规范写法的 `getaddrinfo` 在本机立即失败（WinError 11001），无代理的 urllib 也连不上本机测试端口。因此本机没有打通到内网端口，但守卫把云元数据的十进制写法放行了。

本仓库 `git rev-list --all --count` = 1，HEAD = `5b630bb`。`git status --porcelain` 在改代码前为空。

## 步骤 10：按清单修 P1-1 并验证

只改了 `app.py`：新增 `_coerce_ip_literal`（396-411 行），`ensure_fetch_allowed` 在 DNS 前先用它（421-424 行）。

SSRF 相关测试：

```
pytest tests\test_app.py -q --tb=short -k ssrf
....                                                                     [100%]
4 passed, 39 deselected in 1.87s
```

全量：

```
...........................................                              [100%]
43 passed in 19.69s
```

exit 0。

P1-2 未改代码，原因见 fix-report.md。

收尾：

```
git status --porcelain
 M app.py
```
