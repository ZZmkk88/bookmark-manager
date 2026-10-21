# TASK-045 修复记录

对照审查清单里仍成立的 P2。每条改完跑一次全量 pytest。不修的条目写在后面。

## P2-1 改密文案

- 文件：`README.md:51`，`static/index.html:66`
- 改法：两处「会要求改密码」改为「会提示改密，可以跳过」，与 `README.md:10-11`、`DECISIONS.md:7` 一致。未改接口。
- 验证：

```
E:\muse-bridge\work\TASK-019-bookmark-manager\.venv\Scripts\python.exe -m pytest tests/ -q
```

```
...........................................                              [100%]
43 passed in 18.61s
```

exit 0。

## P2-2 自测示例使用新库

- 文件：`README.md:85-86`、`README.md:91-93`（其后安装节补了健康检查，行号下移 2 行）
- 改法：bash 与 PowerShell 示例设置 `BOOKMARK_DB_PATH` 为 `data/live-selftest.db`（PowerShell 为 `.\data\live-selftest.db`）。PowerShell 注释写明该文件当时还不存在，因为 `tests/live_selftest.py:58-69` 会改掉初始密码。
- 验证：

```
E:\muse-bridge\work\TASK-019-bookmark-manager\.venv\Scripts\python.exe -m pytest tests/ -q
```

```
...........................................                              [100%]
43 passed in 21.12s
```

exit 0。

## P2-3 UPSTREAM 死链

不改。`UPSTREAM.md:20-21` 已指向 README 开篇（`README.md:5-6`）和 `NOTES.md:8` 起的调研笔记。`source_commit`、blob SHA、版权行没有外网可对，不动事实声明。

## P2-4 安装节写上 /health

- 文件：`README.md:53`
- 改法：安装节补一句：`GET /health` 不需要登录，返回 `{"ok":true,"app":"bookmark-manager"}`。函数体未改。删除接口后来插入 6 行，该路由现位于 `app.py:1010-1012`。
- 验证：

```
E:\muse-bridge\work\TASK-019-bookmark-manager\.venv\Scripts\python.exe -m pytest tests/ -q
```

```
...........................................                              [100%]
43 passed in 15.92s
```

exit 0。

## P2-5 删除未使用的 httpx2

- 文件：`requirements-dev.txt:3`（删除后该行是 `pytest==9.1.1`）
- 改法：删掉 `httpx2==2.16.0`。全仓库没有其它 `httpx2` 引用。`httpx==0.28.1` 与 `pytest==9.1.1` 的版本号未改。
- 验证：

```
E:\muse-bridge\work\TASK-019-bookmark-manager\.venv\Scripts\python.exe -m pytest tests/ -q
```

```
...........................................                              [100%]
43 passed in 14.49s
```

exit 0。

## P2-6 删除书签后清掉无引用标签

- 文件：`app.py:763-768`（删除语句仍在 `app.py:761-762`，清理插在提交之前）
- 改法：删掉该书签的关联和书签行之后，删除该用户 `id NOT IN (SELECT tag_id FROM bookmark_tags)` 的 `tags` 行。没有改 `app.py:578-584` 的换标签路径，也没有改测试。
- 验证：

```
E:\muse-bridge\work\TASK-019-bookmark-manager\.venv\Scripts\python.exe -m pytest tests/ -q
```

```
...........................................                              [100%]
43 passed in 13.23s
```

exit 0。

另外用工作目录脚本确认行为（不在仓库里）。两条书签分别带 `keep-me, drop-me` 和 `keep-me`，删掉第一条后标签列表只剩 `keep-me` 且计数为 1。

```
E:\muse-bridge\work\TASK-019-bookmark-manager\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-045-bookmark-manager-p2\check_orphan_tags.py
```

```
{'keep-me': 1}
ORPHAN CHECK PASSED
```

exit 0。

## P2-7 只监听 127.0.0.1

不改。`app.py:34` 默认 `BM_HOST=127.0.0.1`，`app.py:1018` 把该值交给 uvicorn。`DECISIONS.md:37-39` 与 `README.md:60` 已定这个口径。本轮没有再起服务探测 `::1`。另绑 IPv6 会改变已文档化的单地址监听。

## P2-8 密码比较与会话 token

不改。`secrets.compare_digest` 已在 `app.py:270-272` 和 `app.py:305-307`。会话 token 仍明文写入 `app.py:276`。`tests/test_app.py:92` 和 `tests/test_app.py:521` 用登录返回的 token 查询 `sessions.token`。改成只存哈希会让这两条失败，本轮不许改测试。

## 收尾全量测试

全部改完后重跑。命令（仓库根）：

```
E:\muse-bridge\work\TASK-019-bookmark-manager\.venv\Scripts\python.exe -m pytest tests/ -q
```

```
...........................................                              [100%]
43 passed in 12.76s
```

exit 0。`tests/` 不在改动里，没有加 skip / xfail，没有改断言。

## git status --porcelain

命令（仓库根）：

```
git status --porcelain
```

```
 M README.md
 M app.py
 M requirements-dev.txt
 M static/index.html
```
