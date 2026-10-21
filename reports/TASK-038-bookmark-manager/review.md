# bookmark-manager 验收审查

审查时 HEAD 为 `5b630bb`（本克隆只有这 1 个提交）。结论依据是本地命令输出和源码行号。上游 GitHub 上的 commit / blob / 版权原文按任务要求未联网核对，写「未核实」。

## 本地跑通记录

环境：Python 3.11.9（`python --version`）。`py -3 --version` 失败，原文 `Unable to create process using 'E:\python.exe --version'`。README 要求 3.10+，改用 `python`。虚拟环境放在 `E:\muse-bridge\work\TASK-038-bookmark-manager\.venv`，避免仓库里没有 `.gitignore` 时把 `.venv` 算进改动。

安装运行依赖，exit 0：

```
E:\muse-bridge\work\TASK-038-bookmark-manager\.venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-038-bookmark-manager\requirements.txt
```

装上 fastapi==0.156.4、uvicorn==0.54.0、python-multipart==0.0.32。

安装测试依赖，exit 0：

```
E:\muse-bridge\work\TASK-038-bookmark-manager\.venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-038-bookmark-manager\requirements-dev.txt
```

装上 httpx==0.28.1、httpx2==2.16.0、pytest==9.1.1。`httpx2` 能装上，不是安装阻断。

全量测试（cwd = 仓库），exit 0：

```
E:\muse-bridge\work\TASK-038-bookmark-manager\.venv\Scripts\python.exe -m pytest tests -q --tb=short --rootdir E:\muse-bridge\in\TASK-038-bookmark-manager
...........................................                              [100%]
43 passed in 21.60s
```

与 README.md:78「共 43 项」一致。用绝对路径调用 pytest 时 rootdir 落在 `tests/`，会报 `ModuleNotFoundError: No module named 'app'`。那是调用方式错误。按 README 在仓库根目录跑 `pytest tests/` 则通过。

服务：`PORT=8123`，`BOOKMARK_DB_PATH` 指向工作目录 `live.db`，以 `__main__` 跑 `app.py`。日志：

```
INFO:     Uvicorn running on http://127.0.0.1:8123 (Press CTRL+C to quit)
```

首页与健康检查（`http://127.0.0.1:8123`）：

```
GET / -> 200
content-type: text/html; charset=utf-8
content-length: 17098
body 开头: <!DOCTYPE html> ... <title>书签管理器

GET /health -> 200
content-type: application/json
body: {"ok":true,"app":"bookmark-manager"}
```

`tests/live_selftest.py`（`BASE=http://127.0.0.1:8123`）exit 1。失败在外网抓标题，原文：

```
File "...\tests\live_selftest.py", line 120, in main
    status, text = call("POST", "/api/fetch-metadata", ... docs.python.org ...)
TimeoutError: timed out
```

此前断言没有抛 AssertionError。服务日志里登录、改密、再登录、导入、列表、归档、改标签、搜索、导出均为 200。`POST /api/fetch-metadata` 没有完成记录，而之后的 `GET /` 与 `GET /health` 仍是 200。判定为环境限制：本机存在 `HTTP_PROXY=http://127.0.0.1:7890`，服务进程已去掉代理，但 `app.py:364` 的 `getaddrinfo` 没有超时，请求卡在 `app.py:434` 的 `timeout=10` 之前。不计入缺陷，没有第 2 次重试。

跑完后已结束服务进程。未使用 taskkill。

## README 与实际不符处

抽查过且与代码一致、不单列的：监听端口默认 8000（`app.py:1012`）、`BM_HOST` 默认 `127.0.0.1`（`app.py:34`）、数据库默认落在 app.py 旁的 `data/bookmarks.db`（`app.py:28`）、初始账号 admin / admin123（`app.py:30-31`）、Token 24 小时（`app.py:29`）、标题 512 超长拒绝（`app.py:36`、`app.py:141-148`）、标签 64 与 `dropped_tags`（`app.py:37`、`app.py:106-127`）、43 项测试（见上，21.60s 全过）。

1. README.md:51 写「首次登录会要求改密码」。README.md:10-11 写「只提示、不强制，可以跳过」。代码不拦截业务接口（`DECISIONS.md:7-8`；`tests/test_app.py` 的 `test_must_change_is_hint_only` 已通过）。页面有跳过按钮 `static/index.html:79`。同一页 `static/index.html:66` 又写「登录后会要求改密码」，`static/index.html:69` 注释是「强制改密」。以 README.md:10-11 和 DECISIONS 为准，第 51 行和页面第 66 行偏严。按 DECISIONS.md:15-16，不把「未改密仍可调业务接口」当成缺陷。

2. README.md:18-20 写自动抓取会拒绝本机 / 内网 / 链路本地地址，含 `169.254.169.254`，并给出提示。规范写法会拒绝：`app.py:379` 有 `169.254.0.0/16`，`app.py:413-414` 抛 `BlockedUrlError`。非规范 IPv4 不会。本机探针（未打桩）调用 `ensure_fetch_allowed`：`http://127.0.0.1/`、`http://localhost/`、`http://[::1]/` 为 BLOCKED；`http://2852039166/`、`http://2130706433/`、`http://0x7f000001/`、`http://0177.0.0.1/`、`http://127.1/`、`http://0/` 为 ALLOWED。同一台机器上 `socket.inet_aton("2852039166")` 得到 `169.254.169.254`，`socket.inet_aton("2130706433")` 得到 `127.0.0.1`。原因是 `app.py:403-411` 只认 `ipaddress` 的标准写法，认不出就去做 DNS，DNS 失败则直接 return（放行）。本机 Windows 的 `getaddrinfo` / urllib 也连不上这些写法（WinError 11001），所以没有打通到内网端口；守卫仍然没有按 README 拒绝并提示。

3. README.md:20 写「跟随重定向时每一跳都会重新校验」。`app.py:431` 每跳都调用了 `ensure_fetch_allowed`。`app.py:432-434` 真正连接时再次解析。`tests/test_app.py:662-689` 把 `resolve_host_addresses` 打成公网 IP `93.184.216.34`，把 `socket.getaddrinfo` 打到 `127.0.0.1`，断言抓取成功。这证明校验看到的地址和连上的地址可以不是同一个。

4. README 安装与启动（README.md:51）只写打开 `http://localhost:8000`，没有写健康检查。代码有 `app.py:1004-1006` 的 `GET /health`。本次实测返回 200 且 body 为 `{"ok":true,"app":"bookmark-manager"}`。这是文档遗漏，接口本身正常。

## 许可证与署名核查

内部口径一致，外部事实未核实。

- LICENSE:1-3 是 MIT，版权行 `Copyright (c) 2026 ZZmkk88`。
- README.md:102-103 写 MIT，并说明 Linkding 同为 MIT、归因见 UPSTREAM.md。
- UPSTREAM.md:7-8 写 license MIT，attribution 为 `Copyright (c) 2019 Sascha Ißbrücker`。UPSTREAM.md:19-21 与 `app.py:3` 都写独立实现 / clean-room，没有把上游源码抄进仓库的迹象（未与上游逐文件对照，因为禁止访问外网）。
- 独立实现不把上游版权写进自己的 LICENSE，与上述三份声明不冲突。本次不改 LICENSE、不改 UPSTREAM。
- UPSTREAM.md:6 的 `source_commit` `27b7303baf41bb28babc610ac8eaa486e1ddfab5`，以及 UPSTREAM.md:27 的 blob SHA `357447c54f16445a0e4e6cc9b3b89265b4b9fb42`，未核实。
- 本克隆只有提交 `5b630bb`。DECISIONS.md 里的 `62fa2f66`、`f2ec2ec5`、`edcd0df49c1c` 等在本仓库 `git log --all` 中不存在，那些历史声明无法在本地复核。不据此改 DECISIONS.md。

`requirements-dev.txt:3` 的 httpx2==2.16.0 已安装。其 METADATA 写着 BSD-3-Clause、作者信息指向 Pydantic 的 HTTPX2。仓库源码和测试都没有 `import httpx2`。多一个未使用依赖，不是许可证冲突。见下方 P2。

## 分级修复清单

### P0

无。依赖按 README 能装上，43 项测试通过，8123 上首页和 `/health` 返回正常。外网抓标题超时按环境限制处理，不列入 P0。

### P1

1. **非规范 IPv4 绕过抓取守卫。** 文件 `app.py:403-411`（放行分支 `app.py:408-411`）。十进制 `2852039166` 即 `169.254.169.254`，守卫返回 ALLOWED，不给出拒绝提示。修法：在 DNS 之前用 `socket.inet_aton` 把十进制、十六进制、八进制和省略写法收成规范 IPv4，再交给 `_is_public_ip`（`app.py:385-393`）。认不出才按主机名解析。

2. **校验地址没有钉死到实际连接。** 文件 `app.py:426-434`，配合 `app.py:361-365`。同一跳先检查、再连接，两次解析可以不同；`tests/test_app.py:662-689` 就是这条路径。修法：连接使用已经判定为公网的那个 IP，并带上原来的 Host。**本项不改代码**：现有测试故意把两次解析拆开，改了会让该测试失败，而本任务禁止改测试。

### P2

1. README.md:51「会要求改密码」与 README.md:10-11 冲突。修法：改成「会提示改密，可以跳过」。`static/index.html:66` 同样改掉；`static/index.html:69` 注释「强制改密」改成「提示改密」。不改接口行为（DECISIONS.md:15-16）。

2. `app.py:364` 的 `getaddrinfo` 没有超时。外网自测时请求挂住，访问日志一直没有这条 `POST /api/fetch-metadata` 的完成行。修法：给解析加超时，超时按普通抓取失败处理（空标题），不要升成 400，以免断网时「只填网址也能保存」失效。

3. `requirements-dev.txt:3` 的 `httpx2==2.16.0` 没有被源码或测试 import。修法：从开发依赖里去掉这一行。不改其他已有版本号。本次不改，避免动到无关依赖。

4. 导入不检查 URL 长度。`app.py:886-890` 只看 scheme 和主机名；创建接口 `app.py:133` 拒绝长于 2048 的网址。修法：导入时同样按 `MAX_URL_LENGTH` 计入失败。

5. `app.py:408-411` 在主机名解析失败时放行。注释写明是故意的。非规范 IP 修好后，纯主机名解析失败仍会放行。修法：保持，不在本次改。

6. 6to4 内嵌回环未拦截。探针里 `http://[2002:7f00:1::]/` 为 ALLOWED（`ipaddress` 认为它是全球 IPv6）。修法：若 `IPv6Address.sixtofour` / `teredo` 内嵌地址不是公网，则拒绝。本机没有证明操作系统会把它连到 127.0.0.1，所以不升为 P1。
