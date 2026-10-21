# bookmark-manager 验收报告

结论：本机能装上依赖并跑通。pytest 21 项通过；8000 端口首页和 `/health` 返回 200；8123 端口上的 `live_selftest` 通过。没有 P0。需要先处理的是首次改密只挡页面、进程默认绑在 `0.0.0.0`。README 有 8 处和代码或测试对不齐。仓库内部把本项目和上游都写成 MIT，说法互相一致；上游提交哈希和上游许可证原文未在本机核实，本项目版权人与 git 作者对不上。

虚拟环境、数据库、pip 缓存都在 `E:\muse-bridge\work\TASK-006-bookmark-manager`。待审仓库源码未改。

## 本地跑通记录

解释器：`python --version` → `Python 3.11.9`，满足 README 的 3.10+。

依赖（退出码均 0）：

```
E:\muse-bridge\work\TASK-006-bookmark-manager\venv\Scripts\python.exe -m pip install --disable-pip-version-check --cache-dir E:\muse-bridge\work\TASK-006-bookmark-manager\pip-cache -r E:\muse-bridge\in\TASK-006-bookmark-manager\requirements.txt
```

```
Successfully installed ... fastapi-0.156.4 ... python-multipart-0.0.32 starlette-1.9.0 ... uvicorn-0.54.0
```

```
E:\muse-bridge\work\TASK-006-bookmark-manager\venv\Scripts\python.exe -m pip install --disable-pip-version-check --cache-dir E:\muse-bridge\work\TASK-006-bookmark-manager\pip-cache -r E:\muse-bridge\in\TASK-006-bookmark-manager\requirements-dev.txt
```

```
Successfully installed ... httpx-0.28.1 ... pytest-9.1.1
```

pytest（工作目录为仓库根，未设置 `PYTHONPATH`，临时目录改到工作目录）：

```
E:\muse-bridge\work\TASK-006-bookmark-manager\venv\Scripts\python.exe -B -m pytest tests/ -q --tb=short -p no:cacheprovider --basetemp E:\muse-bridge\work\TASK-006-bookmark-manager\pytest-basetemp
```

```
.....................                                                    [100%]
app.py:192
  DeprecationWarning: on_event is deprecated, use lifespan event handlers instead.
fastapi\testclient.py:1
  StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
21 passed, 3 warnings in 4.59s
EXIT:0
```

墙钟 6.10 秒。21 这个数字与 README 一致。3 条是弃用警告。

8000 服务（数据库 `work\...\run8000\bookmarks.db`）：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

```
HEALTH 200 {"ok":true,"app":"bookmark-manager"}
INDEX 200 len 15836 ctype text/html; charset=utf-8
INDEX_HAS_TITLE True
INDEX_HAS_DEFAULT_ACCOUNT True
LOGIN 200 {"token":"58Wf...Brs","username":"admin","must_change_password":true}
GET_BOOKMARKS_JSON_CTYPE 200 {"bookmarks":[],"total":0}
CREATE_BEFORE_PW_CHANGE 201 {"id":1,"url":"https://example.com/probe-before-pw","title":"改密前写入",...}
LOGOUT_JSON_CTYPE_EMPTY 200 {"ok":true}
DELETE_JSON_CTYPE_EMPTY 200 {"ok":true}
```

token 全文留在当次工具输出里，这里只留首尾。首页含「书签管理器」和 `admin / admin123`。带 `Content-Type: application/json` 且没有 body 的 GET、DELETE、logout 都返回 200。

8123 上按 README 的真实数据自测跑了一次（`BASE=http://127.0.0.1:8123`，全新库，退出码 0，2.89 秒）：

```
✓ 导入真实书签：{'total': 9, 'success': 9, 'failed': 0}
✓ 列表（默认不含归档）共 8 条
✓ 归档区有 1 条（Linkding 官网），伪标签已还原成归档状态
✓ 导出成功，文件 1510 字节，含归档伪标签
✓ 真实外网抓取 docs.python.org：status=200 title='3.15.0 Documentation'
LIVE SELFTEST PASSED
```

外网抓取由 `tests/live_selftest.py` 自己发起，一次成功，有标题返回。不记环境限制，也不记缺陷。

结束后两个端口复查均为 `URLError`。`git status --short` 无输出。仓库内不存在 `data`、`__pycache__`、`.pytest_cache`、`.venv`。

与 README 命令的差别：没有在仓库里创建 `.venv`。安装与启动用的是工作目录 venv 的绝对路径，依赖文件和被测代码仍是仓库里的那一份。bash 的 `PORT=8123 .venv/bin/python app.py &` 没有原样贴进 PowerShell。

## README 与实际不符处

1. `README.md:10`、`README.md:43` 写首次登录强制要求改密。`static/index.html:161` 在 `must_change_password` 为真时停在改密页。`app.py:467` 的创建书签不读这个标志。8000 实测未改密 `POST /api/bookmarks` 返回 201。
2. `README.md:8` 写功能「均已测试覆盖」。`tests/test_app.py:146-154` 只断言标题「手动」、网址 `example.com/auto`、标签「教程」。`tests/test_app.py:287` 断言导入结果 `{"total": 4, "success": 2, "failed": 2}`，覆盖坏链接和文件内重复。`README.md:18` 的「已存在则更新」以及描述、备注搜索没有对应断言。另测（工作目录 `extra_checks.py`，退出码 0）里这两项是通的：`SEARCH 独有词甲 1`、`SEARCH 独有词乙 1`、`AFTER_UPDATE 1 [('第二版', '新描述', 'https://example.com/exists/')]`。
3. `README.md:18` 把文件内重复写成「跳过」。`app.py:734` 执行 `result["failed"] += 1`。另测 `IMPORT_INFILE_DUP {'total': 2, 'success': 1, 'failed': 1}`。`tests/test_app.py:287` 也把这类重复算进 `failed`。
4. `README.md:3` 使用「全文搜索」。`app.py:532` 是 `title/url/description/notes/标签名` 的 `LIKE` 子串，库里没有 FTS。`README.md:14` 的「关键词匹配」与这行一致。
5. `README.md:40` 写默认监听 8000，并在 `README.md:43` 让人打开 localhost。`app.py:847` 为 `host="0.0.0.0"`。日志是 `Uvicorn running on http://0.0.0.0:8000`，8123 同样是 `0.0.0.0`。
6. `README.md:50` 把数据库默认值写成 `data/bookmarks.db`。`app.py:25` 的默认路径锚定在 `app.py` 所在目录，不跟进程当前目录走。
7. `README.md:14` 写搜索包含备注。`static/index.html:116` 的占位文案是「搜索标题 / 网址 / 描述 / 标签…」。接口能搜到备注，见第 2 条另测。
8. `README.md:74-75` 的自测命令只有 bash 的 `PORT=` / `BASE=`。同文件 `README.md:49` 给了 PowerShell 的 `$env:PORT` 示例，自测段没有可直接粘贴的 PowerShell 整段。本次用等价环境变量跑通，没有执行 bash 原文。

核对后与代码一致、不记入上面清单的有：依赖版本能安装；pytest 为 21 项；`app.py:26` 的 token 有效期常量是 24 小时（实钟未等满 24 小时，`tests/test_app.py:73-80` 是把 `expires_at` 改成 0）；默认账号 `admin` / `admin123`；归档默认不出现在列表（自测 9 条导入、列表 8 条、归档 1 条）；Netscape 导入导出在 pytest 和 live_selftest 里都通过。未用真实浏览器或 Linkding 再导入导出文件，这项兼容性不记为已证实缺陷。

## 许可证与署名核查

`LICENSE:1` 标题为 `MIT License`，正文是完整的 MIT 授权条款。`LICENSE:3` 版权行为 `Copyright (c) 2026 bookmark-manager contributors`。`README.md:87-88` 写本项目 MIT，并指向 `UPSTREAM.md` 做 Linkding 的归因。`app.py:3` 写 clean-room、灵感来自 Linkding (MIT)。`UPSTREAM.md:19-21` 写独立重写、未复制上游源码。这几处对「本项目 MIT、上游也是 MIT、归因单独成文」的说法一致。

对不上的是本项目作者。本地 `git log` 只有一次提交 `62fa2f6646be9ed9c18738d8408aea522d553097`，作者 `ZZmkk88 <927675399@qq.com>`，时间 `Wed Oct 21 15:39:26 2026 +0800`，说明为 `docs(bookmark-manager): 简化借鉴表述`。`.git/logs/HEAD:1` 记录克隆来源 `https://github.com/ZZmkk88/bookmark-manager.git`（只读了本地 git 记录，没有打开该页面）。`ZZmkk88` 这个名字没有出现在 `LICENSE`、`README.md`、`UPSTREAM.md`。版权人用的是泛称 `bookmark-manager contributors`。

上游部分按文件记载为：`UPSTREAM.md:6` 提交 `27b7303baf41bb28babc610ac8eaa486e1ddfab5`，`UPSTREAM.md:8` 归因 `Copyright (c) 2019 Sascha Ißbrücker`，`UPSTREAM.md:12-18` 称该提交是 2026-10-21 经 GitHub 接口看到的默认分支 HEAD，版权行逐字来自上游 `LICENSE.txt`。本机按任务要求没有访问外网页面，这三项标为未核实。仓库里看不到 Linkding 源码树；「未复制源码」没有和上游做逐行对照，同样未核实。

若独立重写属实，MIT 不要求把上游版权写进本仓库 `LICENSE`，现在这种拆分可以成立。本仓库自己的版权人与唯一提交作者仍然对不上。

## 分级修复清单

### P0

无。依赖可安装，21 项 pytest、首页、`/health`、live_selftest 都已跑通。

### P1

| 位置 | 问题 | 修法 |
|---|---|---|
| `app.py:467`，入口在 `app.py:211`，页面在 `static/index.html:161` | 首次登录的改密只挡页面。持有初始 token 时可以直接创建书签，实测 201。`app.py:277` 改密后也不删除已有 session。 | 在鉴权依赖里拒绝 `must_change_password` 仍为真的业务请求，只放行改密和登出；改密成功后删掉该用户的 session。 |
| `app.py:847`，默认口令 `app.py:28`，登录页 `static/index.html:66` | 进程监听 `0.0.0.0`，默认口令 `admin123` 写在 README 和登录页上。同一网段可以在改密前使用该账号。 | 默认 `host` 改为 `127.0.0.1`，对外监听再另设环境变量。 |

### P2

| 位置 | 问题 | 修法 |
|---|---|---|
| `app.py:192` | 每次启动都有 `on_event` 弃用警告。当前 FastAPI 0.156.4 仍会执行启动逻辑，测试已通过。 | 改成 lifespan，在里面调用 `init_db`。 |
| `requirements-dev.txt:2` | pytest 采集到 Starlette 警告：继续用 httpx 0.28.1 的 TestClient 已弃用，提示安装 `httpx2`。测试仍然 21 通过。 | 按这条警告调整测试客户端依赖，并再跑一遍 pytest。 |
| `README.md:8`，缺口在 `tests/test_app.py:146` 与 `tests/test_app.py:279` | 「均已测试覆盖」多写了。描述/备注搜索和「已存在则更新」没有断言，另测证明功能本身是通的。 | 补上这两类断言，或改掉「均已测试覆盖」这句。 |
| `README.md:18`，`app.py:734` | 文件内重复被说成跳过，计数进了 `failed`。 | 增加单独的跳过计数，或把 README 改成记入失败。 |
| `README.md:3`，`app.py:532` | 开篇写全文搜索，实现是 `LIKE`。 | 开篇改成关键词搜索；若要保留全文搜索，再加 SQLite FTS。 |
| `README.md:50`，`app.py:25` | 默认数据库被写成相对路径 `data/bookmarks.db`，实际锚定在 `app.py` 所在目录。 | README 写明默认文件是 `app.py` 同目录下的 `data/bookmarks.db`。 |
| `README.md:74` | 自测只给了 bash 环境变量写法。 | 补一段 PowerShell：`$env:PORT`、`$env:BASE` 和对应的 `Scripts\python.exe`。 |
| `static/index.html:116`，对照 `README.md:14` | 搜索框占位没有「备注」，接口会搜备注。 | 占位文案补上备注。 |
| `app.py:61` | `http://example.com:80/a` 归一化后仍带 `:80`，与不带端口的地址不会判重。另测输出分别是 `http://example.com:80/a` 和 `http://example.com/a`。 | 归一化时去掉 http 的 80 和 https 的 443。 |
| `app.py:339` | 响应头 `charset="gbk"` 这种带引号的写法匹配不到。另测 `QUOTED_CHARSET_REGEX_MATCH None`。同文件 `app.py:343` 的 meta 正则允许引号。 | 响应头正则同样允许引号，避免带引号的非 UTF-8 页面被当成 UTF-8。 |
| `app.py:94` | 超过 64 字的标签被直接丢掉，接口不说明。 | 在创建或导入结果里返回被丢弃的标签，或在 README 写明上限。 |
| `LICENSE:3` | 版权人是泛称，与唯一提交作者 `ZZmkk88` 对不上。 | 版权行写成实际作者，或在 README 写明作者标识。 |
| `UPSTREAM.md:6` | 上游提交和「版权行逐字复制」未在本机核实。 | 把核对过的上游许可证摘录或校验值放进仓库，便于离线复查。 |
