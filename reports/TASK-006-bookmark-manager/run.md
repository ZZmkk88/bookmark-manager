# TASK-006 bookmark-manager 本地验收运行记录

开工时间：2026-10-21
执行方：Grok Build（本地验收）
工作目录：E:\muse-bridge\in\TASK-006-bookmark-manager
状态：开工。尚未安装依赖、尚未跑测试、尚未起服务。

## 步骤 0：环境探测

命令：

```
python --version
```

输出：

```
Python 3.11.9
```

判定：满足 README「Python 3.10 或更高版本」。

仓库根目录文件（含隐藏）：`.git` `.gitignore` `app.py` `LICENSE` `NOTES.md` `README.md` `requirements.txt` `requirements-dev.txt` `UPSTREAM.md` `static/` `tests/`。

`.gitignore` 已忽略 `.venv/` `data/` `__pycache__/` `.pytest_cache/` `*.db`。

为避免写入待审仓库，虚拟环境、pip 缓存、测试临时目录、运行数据库都放在 `E:\muse-bridge\work\TASK-006-bookmark-manager`，不在仓库内创建 `.venv` 或 `data/`。

## 步骤 1：创建虚拟环境

命令：

```
python -m venv E:\muse-bridge\work\TASK-006-bookmark-manager\venv
```

输出：命令退出码 0，无额外输出。解释器路径：`E:\muse-bridge\work\TASK-006-bookmark-manager\venv\Scripts\python.exe`。

与 README 的差异：README 写的是在项目目录内执行 `python -m venv .venv`。本次因禁止写入仓库源码树，venv 改放到工作目录。随后的 pip / pytest / 启动命令使用该 venv 的绝对路径，安装的依赖文件仍是仓库里的 requirements。

venv 解释器版本：`Python 3.11.9`。

## 步骤 2：安装运行依赖

命令：

```
E:\muse-bridge\work\TASK-006-bookmark-manager\venv\Scripts\python.exe -m pip install --disable-pip-version-check --cache-dir E:\muse-bridge\work\TASK-006-bookmark-manager\pip-cache -r E:\muse-bridge\in\TASK-006-bookmark-manager\requirements.txt
```

退出码：0。

输出片段（版本已解析并安装成功）：

```
Collecting fastapi==0.156.4
Collecting uvicorn==0.54.0
Collecting python-multipart==0.0.32
...
Successfully installed annotated-doc-0.0.5 annotated-types-0.8.0 anyio-4.15.1 click-8.5.0 fastapi-0.156.4 h11-0.16.0 idna-3.20 opentelemetry-api-1.45.1 pydantic-2.14.1 pydantic-core-2.50.1 python-multipart-0.0.32 starlette-1.9.0 typing-extensions-4.16.0 typing-inspection-0.4.4 uvicorn-0.54.0
```

判定：`requirements.txt` 三个钉死版本均可从 PyPI 安装。传递依赖里出现 starlette 1.9.0、pydantic 2.14.1。

## 步骤 3：安装测试依赖

命令：

```
E:\muse-bridge\work\TASK-006-bookmark-manager\venv\Scripts\python.exe -m pip install --disable-pip-version-check --cache-dir E:\muse-bridge\work\TASK-006-bookmark-manager\pip-cache -r E:\muse-bridge\in\TASK-006-bookmark-manager\requirements-dev.txt
```

退出码：0。

输出片段：

```
Collecting httpx==0.28.1
Collecting pytest==9.1.1
...
Successfully installed certifi-2026.10.19 colorama-0.4.6 httpcore-1.0.9 httpx-0.28.1 iniconfig-2.3.1 packaging-26.3 pluggy-1.7.0 pygments-2.21.0 pytest-9.1.1
```

`requirements-dev.txt` 第一行 `-r requirements.txt` 被 pip 解析，运行依赖显示 already satisfied。pytest 9.1.1 与 httpx 0.28.1 安装成功。

## 步骤 4：跑 pytest

为避免把 `__pycache__`、`.pytest_cache`、测试库写进仓库或系统 TEMP，用工作目录里的脚本设置 `TEMP`/`TMP`/`PYTHONDONTWRITEBYTECODE` 后再执行与 README 等价的 `python -m pytest tests/ -q`。未设置 `PYTHONPATH`。

命令：

```
E:\muse-bridge\work\TASK-006-bookmark-manager\venv\Scripts\python.exe -B E:\muse-bridge\work\TASK-006-bookmark-manager\run_pytest.py
```

脚本实际执行：

```
E:\muse-bridge\work\TASK-006-bookmark-manager\venv\Scripts\python.exe -B -m pytest tests/ -q --tb=short -p no:cacheprovider --basetemp E:\muse-bridge\work\TASK-006-bookmark-manager\pytest-basetemp
```

工作目录：`E:\muse-bridge\in\TASK-006-bookmark-manager`。退出码：0。耗时：脚本统计 ELAPSED_SEC 6.10；pytest 自己报告 4.59s。

输出片段：

```
.....................                                                    [100%]
============================== warnings summary ===============================
app.py:192
  DeprecationWarning: on_event is deprecated, use lifespan event handlers instead.
    @app.on_event("startup")
fastapi\applications.py:4723
  DeprecationWarning: on_event is deprecated, use lifespan event handlers instead.
fastapi\testclient.py:1
  StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
21 passed, 3 warnings in 4.59s
EXIT:0
```

判定：21 项全部通过，与 README「共 21 项」数量一致。3 条是弃用警告，不是失败。

随后 `git status --short` 在仓库根目录无输出、退出码 0，测试没有改动仓库工作区。

## 步骤 5：按默认端口 8000 起服务并检查首页 / 健康检查

数据库放到工作目录，避免在仓库里生成 `data/bookmarks.db`。

命令：

```
E:\muse-bridge\work\TASK-006-bookmark-manager\venv\Scripts\python.exe -B E:\muse-bridge\work\TASK-006-bookmark-manager\start_server.py 8000 E:\muse-bridge\work\TASK-006-bookmark-manager\run8000\bookmarks.db
```

服务日志片段：

```
INFO:     Started server process [27260]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

同时出现 `app.py:192 DeprecationWarning: on_event is deprecated`。监听地址是 `0.0.0.0:8000`，不是仅 127.0.0.1。

探测命令：

```
E:\muse-bridge\work\TASK-006-bookmark-manager\venv\Scripts\python.exe -B E:\muse-bridge\work\TASK-006-bookmark-manager\probe_http.py http://127.0.0.1:8000
```

退出码：0。输出片段：

```
HEALTH 200 {"ok":true,"app":"bookmark-manager"}
INDEX 200 len 15836 ctype text/html; charset=utf-8
INDEX_HAS_TITLE True
INDEX_HAS_DEFAULT_ACCOUNT True
LOGIN 200 {"token":"...","username":"admin","must_change_password":true}
GET_BOOKMARKS_JSON_CTYPE 200 {"bookmarks":[],"total":0}
CREATE_BEFORE_PW_CHANGE 201 {"id":1,"url":"https://example.com/probe-before-pw","title":"改密前写入",...}
LOGOUT_JSON_CTYPE_EMPTY 200 {"ok":true}
DELETE_JSON_CTYPE_EMPTY 200 {"ok":true}
```

判定：
- `/health` 返回 200 且 `ok=true`。
- `/` 返回 200 的首页 HTML，含标题「书签管理器」和默认账号文案。
- 首次登录 `must_change_password=true`，但未改密即可 `POST /api/bookmarks` 得到 201。
- 前端那种带 `Content-Type: application/json` 且无 body 的 GET / DELETE / logout，服务端均返回成功，不是 422。

探测结束后已停止该服务进程（未使用 taskkill）。停止后该任务状态为 cancelled，持续时间 28.82s（含启动后的空闲）。

## 步骤 6：pytest 没覆盖到的本地行为

命令：

```
E:\muse-bridge\work\TASK-006-bookmark-manager\venv\Scripts\python.exe -B E:\muse-bridge\work\TASK-006-bookmark-manager\extra_checks.py
```

数据库：`E:\muse-bridge\work\TASK-006-bookmark-manager\extra-db\extra.db`。退出码：0。未访问外网。

输出片段：

```
NORMALIZE_PORT http://example.com:80/a
NORMALIZE_NOPORT http://example.com/a
NORMALIZE_HOSTCASE https://example.com/A
QUOTED_CHARSET_REGEX_MATCH None
CREATE 201
SEARCH 独有词甲 1
SEARCH 独有词乙 1
SEARCH 只有标题 1
IMPORT_FIRST {'total': 1, 'success': 1, 'failed': 0}
IMPORT_SECOND {'total': 1, 'success': 1, 'failed': 0}
AFTER_UPDATE 1 [('第二版', '新描述', 'https://example.com/exists/')]
IMPORT_INFILE_DUP {'total': 2, 'success': 1, 'failed': 1}
```

另有 StarletteDeprecationWarning：`Using httpx with starlette.testclient is deprecated; install httpx2 instead.`

## 步骤 7：8123 端口与 live_selftest

命令：

```
E:\muse-bridge\work\TASK-006-bookmark-manager\venv\Scripts\python.exe -B E:\muse-bridge\work\TASK-006-bookmark-manager\start_server.py 8123 E:\muse-bridge\work\TASK-006-bookmark-manager\run8123\bookmarks.db
```

服务日志片段：

```
INFO:     Started server process [21008]
INFO:     Uvicorn running on http://0.0.0.0:8123 (Press CTRL+C to quit)
```

自测命令（脚本设置 `BASE=http://127.0.0.1:8123` 后执行仓库里的 `tests/live_selftest.py`）：

```
E:\muse-bridge\work\TASK-006-bookmark-manager\venv\Scripts\python.exe -B E:\muse-bridge\work\TASK-006-bookmark-manager\run_live.py
```

退出码：0。ELAPSED_SEC: 2.89。只跑了这一次。

输出片段：

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

服务端对应日志以 `POST /api/fetch-metadata HTTP/1.1 200 OK` 结束。外网抓取这一步由项目自测发起，返回了标题，不记为环境限制，也不记为缺陷。

## 步骤 8：关服务并确认仓库没被写

8123 服务已停止。复查命令：

```
E:\muse-bridge\work\TASK-006-bookmark-manager\venv\Scripts\python.exe -B E:\muse-bridge\work\TASK-006-bookmark-manager\check_ports.py
```

输出：

```
DOWN http://127.0.0.1:8000/health URLError
DOWN http://127.0.0.1:8123/health URLError
```

`git -C E:\muse-bridge\in\TASK-006-bookmark-manager status --short` 无输出，退出码 0。

`Test-Path` 对仓库内 `data`、`__pycache__`、`tests\__pycache__`、`.pytest_cache`、`.venv` 均为 False。

pip 与创建 venv 未单独计时。pytest 墙钟 6.10 秒（pytest 报告 4.59 秒）。live_selftest 墙钟 2.89 秒。
