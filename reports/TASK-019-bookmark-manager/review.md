# bookmark-manager 验收

服务和自动化测试能跑通。pytest 29 项全部通过，默认端口 8000 的首页和 `/health` 返回正常，8123 上的 live selftest 通过。要修的阻断项只有 1 条：首次登录点「稍后再说」会调用不存在的 `loadAll`。没有达到 P1（安全、数据、权限）且又可以安全改动的项。未改密仍能调业务接口，按 `DECISIONS.md` 销项，不改回强制拦截。

## 本地跑通记录

环境：Python 3.11.9。虚拟环境放在 `E:\muse-bridge\work\TASK-019-bookmark-manager\.venv`（仓库没有 `.gitignore`，任务禁止 `rm`/`del`，不把 `.venv` 放进仓库）。依赖按 README 安装，exit 0：`fastapi-0.156.4`、`uvicorn-0.54.0`、`python-multipart-0.0.32`、`httpx-0.28.1`、`httpx2-2.16.0`、`pytest-9.1.1`。

修复前全量测试。命令：

```
E:\muse-bridge\work\TASK-019-bookmark-manager\.venv\Scripts\python.exe -m pytest tests/ -q
```

输出：

```
.............................                                            [100%]
29 passed in 16.84s
```

默认端口。数据库用工作目录里的 `run-8000.db`，不在仓库里生成 `data/bookmarks.db`。启动日志：

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

探测 `http://127.0.0.1:8000/` 为 200，`Content-Type: text/html; charset=utf-8`，正文以 `<!DOCTYPE html>` 开头，标题是「书签管理器 · bookmark-manager」。`http://127.0.0.1:8000/health` 为 200，正文 `{"ok":true,"app":"bookmark-manager"}`。

同一进程上，`http://localhost:8000/health` 也是 200。`localhost` 的地址顺序是先 `127.0.0.1` 后 `::1`。TCP 连 `::1:8000` 被拒绝（WinError 10061）。没有浏览器工具，没有把浏览器打不开记成已复现。

8123、新库 `run-8123.db`，启动日志：

```
INFO:     Uvicorn running on http://127.0.0.1:8123 (Press CTRL+C to quit)
```

`tests/live_selftest.py`（`BASE=http://127.0.0.1:8123`）exit 0，末行 `LIVE SELFTEST PASSED`。外网抓取原文：`真实外网抓取 docs.python.org：status=200 title='3.15.0 Documentation'`。这一步成功，不算环境限制，没有重试。

两个服务都已停掉。停后 `127.0.0.1:8000` 与 `localhost:8000` 均为 WinError 10061 拒绝连接。

完整命令在 `run.md`。

## README 与实际不符处

下列几条是对得上的，不展开：Token 24 小时（`app.py:27`）、默认账号 admin/admin123（`app.py:28-29`）、默认绑 `127.0.0.1:8000`（`app.py:32`、`app.py:885`，启动日志已证实）、数据库默认路径在 app.py 旁的 `data/bookmarks.db`（`app.py:26`）、标签清洗与 64 字丢弃（`app.py:100-126`）、搜索字段（`app.py:558-561`）、导入「已存在则更新 / 文件内重复算跳过」（`app.py:769-801`）、og 兜底（`app.py:404-405`）、29 项测试（上面的 pytest 输出）。

1. `README.md:47` 写「首次登录会要求改密码」。同文件 `README.md:10-11` 写「只提示、不强制，可以跳过继续使用」。代码不拦截业务接口：`tests/test_app.py:352-357` 在 `must_change_password is True` 时断言 `GET /api/bookmarks` 为 200、`POST /api/bookmarks` 为 201。页面上有跳过按钮 `static/index.html:79`，提示文案在 `static/index.html:72`。登录页 `static/index.html:66` 也写成「登录后会要求改密码」，和下一屏的「可以先跳过」不一致。`DECISIONS.md:5-8` 已规定只提示。
2. `README.md:10-11` 说跳过后可以继续使用。`static/index.html:208` 写的是 `loadAll()`。全仓库只有这一处 `loadAll`，没有这个函数。列表加载函数是 `static/index.html:267` 的 `refresh()`。点「稍后再说」会在浏览器里抛 `ReferenceError`，标签和书签列表不会自动加载。这条同时是下面的 P0。
3. `UPSTREAM.md:20-21` 写对照见 README 的「与 Linkding 的关系」一节。README 的标题只有 `README.md:8`、`README.md:25`、`README.md:58`、`README.md:89`、`README.md:96`，没有这一节。调研笔记实际在 `NOTES.md:8` 起。
4. `README.md:75` 要求 live selftest 使用全新数据库。`README.md:83-86` 的 PowerShell 只设了 `PORT` 和 `BASE`，没有新的 `BOOKMARK_DB_PATH`，也没有清库。库一旦改过密码，`tests/live_selftest.py:58` 用 admin/admin123 登录会失败。本次是用新库跑通的，不是沿用旧库。
5. README 功能清单和安装节都没写健康检查。`app.py:877-879` 有 `GET /health`，本次返回 200。这是遗漏，不是写反。

## 许可证与署名核查

仓库内部的许可证类型是对齐的。`LICENSE:1-3` 为 MIT，版权行 `Copyright (c) 2026 ZZmkk88`，后文是标准 MIT 许可与免责声明（`LICENSE:5-21`）。`README.md:98` 也写 MIT。本仓库版权人只出现在 LICENSE，README、UPSTREAM、`app.py` 没有另一个本仓库版权人。

上游署名单独放在 UPSTREAM，和「本仓库 MIT + 自己的版权行」不打架。`UPSTREAM.md:7-8` 记 Linkding 为 MIT，版权行 `Copyright (c) 2019 Sascha Ißbrücker`。`README.md:98-99` 指向该文件。`app.py:3` 写 clean-room、inspired by Linkding (MIT)。`NOTES.md:44` 写自己重写全部代码。`UPSTREAM.md:3` 用了「复刻学习作品」，`UPSTREAM.md:19` 限定为独立重写、未复制上游源码。本仓库是单文件 FastAPI，不是上游那种 Django 工程布局。

未核实：`UPSTREAM.md:6` 的 `source_commit`（`27b7303baf41bb28babc610ac8eaa486e1ddfab5`）和 `UPSTREAM.md:27` 的 blob SHA（`357447c54f16445a0e4e6cc9b3b89265b4b9fb42`）。任务禁止抓取外部页面，没有对照 GitHub。因此不改 LICENSE，也不改这两行事实声明。

确凿的文档错误只有不符处第 3 条：`UPSTREAM.md:20-21` 指向的 README 小节不存在。这是 P2，本轮不改 UPSTREAM。

## 分级修复清单

### P0

1. `static/index.html:208` 点击「稍后再说」调用不存在的 `loadAll()`，跳过改密后的主界面不会加载列表。修法：改成调用同文件已有的 `refresh()`。

### P1

无。

不列入缺陷：未改密仍可调用书签接口。`DECISIONS.md:15-16` 写明后续审查不得改回强制拦截，`tests/test_app.py:342-357` 锁着这个行为。改回去会直接让测试失败，而且任务不许改测试。

不修 SSRF：`app.py:385` 的 `urlopen` 会请求调用方给出的 http(s) 地址，测试 `tests/test_app.py:256-259` 依赖抓取 `127.0.0.1`。封禁回环地址会弄红现有测试。

### P2

1. `README.md:47` 与 `static/index.html:66` 写成「会要求改密码」。修法：改成「会提示改密，可以跳过」，与 `README.md:10` 和 `DECISIONS.md:7` 一致。不改接口。
2. `README.md:83-86` 的自测命令没有全新数据库。修法：示例里设一个新的 `BOOKMARK_DB_PATH`。
3. `UPSTREAM.md:20-21` 指向不存在的 README 小节。修法：改成指向 `NOTES.md`。不动 commit、blob、版权行。
4. `app.py:877` 的 `GET /health` README 没写。修法：安装节补一句。
5. `requirements-dev.txt:3` 的 `httpx2==2.16.0` 没有任何源码 import。本次安装成功，pytest 不依赖它。修法：确认不需要后删掉这一行。不改其它依赖的版本号。
6. `app.py:633-641` 删除书签后，不再被引用的 `tags` 行还在。修法：删书签后清掉没有关联的标签。书签本身没有丢。
7. `app.py:32` 与 `app.py:885` 只监听 `BM_HOST`（默认 `127.0.0.1`）。本机 TCP `::1:8000` 被拒绝，但 urllib 访问 `http://localhost:8000/health` 仍是 200。修法：若要照顾只走 IPv6 的客户端，再监听 `::1`。没有浏览器复现，本轮不改。
8. `app.py:258` 用 `!=` 比较密码哈希，`app.py:261-263` 把会话 token 明文写入 `sessions`。修法：改为 `compare_digest`，库里只存 token 哈希。单用户本地库，本轮不改。
