# bookmark-manager P2 复核

对照 `E:\muse-bridge\out\TASK-019-bookmark-manager\review.md` 的 P2 八条，在当前仓库逐条核对。P0/P1 没有复发。基线测试 43 项通过。本轮只改仍成立、且改了不会撞上现有测试或已拍板决策的条目。

## 证据

基线命令（仓库根，venv 为上一轮已有环境）：

```
E:\muse-bridge\work\TASK-019-bookmark-manager\.venv\Scripts\python.exe -m pytest tests/ -q
```

```
...........................................                              [100%]
43 passed in 14.82s
```

改代码前 `git status --porcelain` 无输出。

上一轮 P0 已不在。`static/index.html:209` 是 `$("skipChangeBtn").onclick = () => { show("appView"); refresh(); };`，`refresh` 定义在 `static/index.html:269`。全仓库没有 `loadAll`。

## 逐条

### P2-1 仍在：文案写成「会要求改密码」

`README.md:51`：`首次登录会要求改密码。`
`static/index.html:66`：`登录后会要求改密码。`

同文件已经写了相反口径：`README.md:10-11`「只提示、不强制，可以跳过继续使用」；`static/index.html:72`「也可以先跳过」；`DECISIONS.md:5-8` 只提示、不拦截。`tests/test_app.py:595-604` 只断言跳过按钮和退出按钮还在，没有锁死「会要求改密码」这句。

修法：两处改成「会提示改密，可以跳过」。不改接口。

### P2-2 仍在：自测示例没有全新数据库

`README.md:80` 要求「全新数据库」。`tests/live_selftest.py:4` 和 `tests/live_selftest.py:58` 用初始账号 `admin/admin123` 登录，改密后旧库不能再跑（`tests/live_selftest.py:64-69`）。示例 `README.md:83-84`、`README.md:89-90` 只设了 `PORT` 和 `BASE`，没有 `BOOKMARK_DB_PATH`。库路径由 `app.py:28` 读这个环境变量，缺省是 app.py 旁的 `data/bookmarks.db`。

修法：bash 和 PowerShell 示例都设一个新的 `BOOKMARK_DB_PATH`，并写明该文件当时还不存在。

### P2-3 已不在：UPSTREAM 不再指向不存在的小节

`UPSTREAM.md:20-21` 现在写的是「具体对照见 README 开篇的简要说明段落和 NOTES.md 的调研笔记」。`README.md:5-6` 就是这段开篇，`NOTES.md:8` 起是调研笔记。上一轮说的「与 Linkding 的关系」死链已经不在。

`UPSTREAM.md:6` 的 `source_commit` 和 `UPSTREAM.md:27` 的 blob SHA 本轮没有外网可对，不改。LICENSE 不改。

### P2-4 仍在：安装节没写 `/health`

`app.py:1004-1006` 有 `GET /health`，返回 `{"ok": true, "app": "bookmark-manager"}`。`tests/test_app.py:502-505` 锁着这个响应。`README.md:78` 只在测试名单里出现「健康检查」四个字，安装节 `README.md:29-60` 没有这个路由。

修法：安装节补一句，不改路由。

### P2-5 仍在：`httpx2` 没有任何引用

`requirements-dev.txt:3` 是 `httpx2==2.16.0`。全仓库只有这一行出现 `httpx2`，没有 import。同文件 `httpx==0.28.1` 和 `pytest==9.1.1` 保留，其它依赖的版本号不动。

修法：删掉 `httpx2==2.16.0` 这一行。

### P2-6 仍在：删书签后不再被引用的标签行还在

`app.py:761-762` 只删 `bookmark_tags` 和 `bookmarks`，没有删 `tags`。`tags` 表（`app.py:201-208`）没有指向书签的外键。`app.py:773-776` 的标签列表是 `LEFT JOIN`，计数为 0 的标签仍会返回。`tests/test_app.py:207-220` 只检查书签 404 和「新标签」仍在列表里，不要求保留零引用标签。

修法：只在删除接口里清掉该用户已经没有任何 `bookmark_tags` 的标签。不改更新书签时的换标签路径（`app.py:578-584`），那不在本条里。

### P2-7 不改：只监听 `BM_HOST`

`app.py:34` 默认 `127.0.0.1`，`app.py:1012` 把这个值传给 uvicorn。`README.md:58` 和 `DECISIONS.md:37-39`、`DECISIONS.md:50` 已经把「默认只绑 127.0.0.1、用 `BM_HOST` 放开」定死。上一轮报告写过本机 `::1:8000` 被拒绝，但 `http://localhost:8000/health` 经 IPv4 仍是 200，并写明本轮不改。本轮没有再起服务做 TCP 探测，不把上一轮的 WinError 10061 写成这次复现。再绑 `::1` 会改掉已文档化的单地址监听，没有新的阻断证据。

### P2-8 不改：哈希比较已在，token 不能改成只存哈希

`app.py:270-272` 和 `app.py:305-307` 已经用 `secrets.compare_digest` 比较密码哈希。上一轮写的 `!=` 比较不在了。

会话仍是明文：`app.py:274-277` 把 `token_urlsafe` 写入 `sessions.token`，`app.py:250-253` 按明文查询。测试按这个形态写死：`tests/test_app.py:92`、`tests/test_app.py:521` 用登录返回的 token 去 `WHERE token = ?`。改成只存哈希会让这两条失败，而本轮不许改测试。单用户本地库，上一轮也写了不改。

## 分级修复清单

### P0

无。

### P1

无。未改密仍可调业务接口，按 `DECISIONS.md:15-16` 销项，不改回拦截。

### P2（本轮修，按原报告顺序）

1. `README.md:51`、`static/index.html:66`。两处「会要求改密码」改成「会提示改密，可以跳过」。
2. `README.md:83-84`、`README.md:89-90`。自测命令加上新的 `BOOKMARK_DB_PATH`，并说明文件当时还不存在。
3. `README.md:51` 之后的安装节。补一句 `GET /health` 的返回，对应 `app.py:1004-1006`。
4. `requirements-dev.txt:3`。删除未被引用的 `httpx2==2.16.0`。
5. `app.py:761-763`。删除书签提交前，清掉该用户没有关联的 `tags` 行。

### P2（不修）

1. `UPSTREAM.md:20-21` 死链已不在。commit / blob / 版权行未核实，不动。
2. `app.py:34`、`app.py:1012` 的单地址监听是已定口径，不另绑 `::1`。
3. `app.py:274-277` 的明文 token 被 `tests/test_app.py:92` 和 `tests/test_app.py:521` 锁住；`compare_digest` 已在 `app.py:270`。不改。

行号是改代码前的位置。P2-6 在删除接口插入 6 行之后，`GET /health` 在 `app.py:1010-1012`，`uvicorn.run` 在 `app.py:1018`。改动与每次测试结果见 `fix-report.md`。
