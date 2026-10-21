# bookmark-manager 修复验收

## 结论

清单里的 3 条严重问题和 6 条一般项都已改完。pytest 全绿。未登录访问文档接口不是 200。默认只监听 `127.0.0.1`。

- 全量 pytest 退出码 0：`25 passed, 1 warning in 4.62s`（原 21 项仍在，新增 4 项）。
- 未设置 `HOST` 时，日志为 `Uvicorn running on http://127.0.0.1:62755`，`netstat` 只有 `127.0.0.1:62755` 在 LISTENING。
- 未带令牌：`GET /docs`、`/redoc`、`/openapi.json` 都是 404。
- 默认口令登录后、尚未改密：`GET /api/bookmarks` 为 403，`GET /api/me` 为 200。

逐条改法、行号和命令见仓库 `fix-report.md`（与本目录同文）。

## pytest

工作目录 `E:\muse-bridge\in\TASK-004-bookmark-manager-fix`。解释器 `E:\muse-bridge\env\bookmark-manager\Scripts\python.exe`。

```text
E:\muse-bridge\env\bookmark-manager\Scripts\python.exe -m pytest -q --tb=short
```

退出码 0。

```text
.........................                                                [100%]
============================== warnings summary ===============================
..\..\env\bookmark-manager\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\env\bookmark-manager\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
25 passed, 1 warning in 4.62s
```

这条警告来自当前环境的 Starlette TestClient。上一轮 `app.py` 的 `on_event` 弃用警告这次没有再出现。

改密相关的三条在合入其余改动之前单独跑过：`3 passed, 19 deselected, 3 warnings in 1.63s`。当时 `on_event` 还在，所以仍有 3 条警告。

## 短时进程

`E:\muse-bridge\work\TASK-004-bookmark-manager-fix\bindcheck.py` 去掉 `HOST`，数据库放在该工作目录，退出码 0。

```text
HEALTH 200 {"ok":true,"app":"bookmark-manager"}
DOCS 404
REDOC 404
OPENAPI 404
LOGIN 200 must_change_password=true（token 43 字符，记录里已抹掉）
LIST 403 {"detail":"请先修改密码"}
ME 200 {"username":"admin","must_change_password":true}
TCP    127.0.0.1:62755        0.0.0.0:0              LISTENING       25836
Uvicorn running on http://127.0.0.1:62755
AFTER_STOP ConnectTimeout: timed out
```

之后 `netstat -ano | findstr 62755` 只剩 `TIME_WAIT`，没有 LISTENING。仓库下没有新增 `data\`。

## 三条严重项

1. **未改密拦截，改密作废旧会话。** `app.py:234-239` 对业务路径返回 403。`app.py:295-302` 删除该用户全部 session 并返回新 token。`static/index.html:185-193` 把新 token 写回 `localStorage`。用例 `tests/test_app.py:61`、`tests/test_app.py:79` 已通过。短时进程上列表是 403。
2. **监听地址。** `app.py:871` 使用 `HOST`，默认 `127.0.0.1`。`README.md:47` 写入了该变量。用例 `tests/test_app.py:384` 覆盖默认值和 `HOST=0.0.0.0`。短时进程的日志和 `netstat` 都是 `127.0.0.1`。
3. **LICENSE。** `LICENSE:23-28` 增加 NOTICE：独立实现，沿用 Linkding（MIT）的归档伪标签和 `[linkding-notes]`，并写明「上游版权行待从 sissbruecker/linkding 的 LICENSE 原样补入」。没有联网，没有凭记忆写版权人。

## 清单内的一般项

4. `app.py:551-558` 对 `q` 转义 `\` `%` `_`，`LIKE` 使用 `ESCAPE '\'`。`README.md:4` 改为「关键词搜索」。`tests/test_app.py:190` 已通过：`q=%` 只命中含字面量 `%` 的那一条。
5. `README.md:38-41` 改为 `HOST` / `PORT`，未设置时写 `http://127.0.0.1:8000`。
6. `app.py:200-202` 关闭 `docs_url`、`redoc_url`、`openapi_url`。未授权访问为 404（用例与短时进程一致）。
7. `app.py:191-195` 改为 lifespan，启动时仍调用 `init_db()`。全量 pytest 不再报 `on_event` 弃用。
8. `README.md:27` 补上「同一文件内重复的归一化网址计为 failed，不覆盖先出现的那条」。导入实现未改。原导入用例仍通过。
9. `NOTES.md:6` 改为「依赖见 requirements.txt」。本机实测 fastapi `0.153.0`、uvicorn `0.54.0`、httpx `0.28.1`、pytest `9.1.1`，与原先写的 `0.156.4` 不同，所以没有把版本号写回去。

`README.md:56` 的条数改为 25，用来对准新增用例。

## 本轮没有改的上一轮意见

互通说法、有标题就不抓描述、搜索框占位文案、只有 Unix 的安装说明、测试共用一个模块级数据库。这些不在本轮清单里。

## 没有做的检查

- 没有浏览器工具。改密后页面是否把新 token 写进 `localStorage`，只核对了 `static/index.html:185-193`，没有在浏览器里点击。
- `tests/live_selftest.py:115-116` 会请求 `https://docs.python.org/3/`。按禁止外网，没有跑。标为环境限制。
- Linkding 上游 LICENSE 原文未核实。
