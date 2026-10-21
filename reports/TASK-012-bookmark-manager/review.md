# bookmark-manager 验收报告

结论：本机能装起并跑通。pytest 21 项全过；不设 `PORT` 时监听 8000，`/` 与 `/health` 均 HTTP 200；按 README 用 8123 跑 `tests/live_selftest.py` 通过，外网抓标题也成功。没有 P0。P1 有 3 条，本次改前 2 条（数据接口不强制改密、默认监听 `0.0.0.0`）。第 3 条（改密不撤销其他会话）会破坏现有测试，不改代码。

证据命令与原文在 `run.md`。下面只引片段。行号均指审查时的源码。

## 本地跑通记录

环境：Python 3.11.9（`python --version`）。`py -3` 指向无效的 `E:\python.exe`，未使用。虚拟环境放在 `E:\muse-bridge\work\TASK-012-bookmark-manager\.venv`，没有写进仓库。依赖用该 venv 执行 `pip install -r requirements-dev.txt`（内含 `-r requirements.txt`），退出码 0。装上的版本与钉扎一致：fastapi 0.156.4、uvicorn 0.54.0、python-multipart 0.0.32、httpx 0.28.1、pytest 9.1.1。无依赖冲突。

测试命令（仓库根目录）：

```
E:\muse-bridge\work\TASK-012-bookmark-manager\.venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

输出片段：

```
21 passed, 3 warnings in 4.37s
```

退出码 0。警告是 `app.py:192` 的 `on_event` 弃用，以及 Starlette 提示 `httpx` TestClient 弃用，不是失败。`tests/test_app.py:10` 使用 `tempfile.mkdtemp`，这次 pytest 的临时库落在进程 TEMP（改 `TEMP` 的命令被本机会话策略拦住）。服务用的数据库在 work 目录：`default-8000.db`、`live-8123.db`。

服务：监督脚本 `run_flow.py` 用 venv 启动仓库 `app.py`。第一次不设 `PORT`。日志：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

`GET http://127.0.0.1:8000/health` → `200 {"ok":true,"app":"bookmark-manager"}`。`GET /` → 200，HTML 含 `<title>书签管理器`，长度 15183，正文含 `admin123`。

第二次 `PORT=8123`、全新库，再跑 `tests/live_selftest.py`（`BASE=http://127.0.0.1:8123`）。退出码 0，耗时 8.86 秒，末行 `LIVE SELFTEST PASSED`。外网抓取一次成功：`status=200 title='3.15.0 Documentation'`。没有重试。

跑完后脚本 `terminate()` 子进程。Windows 上因此 returncode 为 1，日志没有 traceback。之前另有一次后台启动，在 `/` 与 `/health` 已返回 200 后进程自己退出（退出码 1，无 traceback），不以那次作为失败结论。

同一轮还记录了这些行为（完整 JSON 见 `run.md`）：

- 登录 `admin/admin123` 返回 `must_change_password=true`，此时 `GET /api/bookmarks` 仍是 200。
- 标签串为 65 个 `x` 加 `,ok-tag`，创建返回 201，`tags` 只有 `["ok-tag"]`。
- `notes=独特备注ZZZ` 后按该词搜索，`total=1`。
- 改密后，另一个仍未过期的 token 访问 `GET /api/me` 仍是 200。
- `q=' OR 1=1 --` 返回 200 且 `total=0`，没有拼进 SQL。
- `GET /docs` 返回 200。

## README 与实际不符处

以下声称和代码一致，不单列缺陷：21 项测试（pytest 输出 `21 passed`，README.md:69）；默认端口 8000（不设 `PORT` 的启动日志，README.md:31、49，app.py:847）；初始账号 admin/admin123（README.md:43、51，app.py:27-28）；库路径环境变量 `BOOKMARK_DB_PATH`（README.md:50，app.py:25）；抓取顺序先 `<title>` / `meta description` 再 og（README.md:12，app.py:381-382）；新建时归一化网址重复返回 409（README.md:12，app.py:487-488）；标签去空格、空格转连字符、忽略大小写去重（README.md:13，app.py:81-101）；归档默认不进列表（README.md:16，app.py:518-521）；导入已存在则更新（README.md:18，app.py:744-752）。导出是否真能被「任何浏览器或 Linkding」导入（README.md:19）本次没有拿外部程序对照，不判为已证实的不符。

不符：

1. README.md:9 写功能「均已测试覆盖」。实际没有对应用例的包括：`POST /api/logout`（app.py:255）、`GET /health`（app.py:839）、`POST /api/fetch-metadata` 这个路由（app.py:394；test_app.py:243 只直接调用 `fetch_metadata`）、搜索描述和备注（README.md:14；test_app.py:146-154 只断言标题、网址、标签名）、Token「24 小时」这个数值（README.md:10，常量在 app.py:26；test_app.py:76 只把 `expires_at` 改成 0）。备注搜索本身可用，见上一节探测，这是覆盖缺口，不是功能缺失。README 未写 `/health`，代码有 app.py:839-841，属文档遗漏。

2. README.md:10、43 写首次登录会要求改密码（「强制提示」）。前端在 `must_change_password` 时只显示改密页（static/index.html:160-161）。后端 `current_user`（app.py:211-227）不看这个标志，数据接口照常执行。探测：标志为 true 时 `GET /api/bookmarks` 返回 200。

3. README.md:18 写导入时「文件内重复跳过」，并返回总数/成功/失败。代码把文件内重复计入 `failed`（app.py:733-735），没有单独的跳过字段。这与 test_app.py:287 的期望一致。页面把同一个数字说成「失败/跳过」（static/index.html:356）。

4. README.md:43 让用户打开 localhost，环境变量表（README.md:47-51）没有监听地址。app.py:847 固定 `host="0.0.0.0"`。启动日志是 `Uvicorn running on http://0.0.0.0:8000`。

5. README.md:71 写真实数据自测「两个系统同理」，紧接着的命令只有 bash 的 `PORT=8123 ... &`（README.md:74-75）。PowerShell 安装示例在 README.md:36-41，自测节没有对应写法。

6. README.md:14 写搜索含备注，查询也含 `b.notes`（app.py:532）。搜索框占位文案没有「备注」（static/index.html:116）。

## 许可证与署名核查

仓库内部三条声明可以同时成立，没有第二套版权人：

- LICENSE:1-3 为 MIT，版权行 `Copyright (c) 2026 bookmark-manager contributors`。正文是常见 MIT 许可，未见改过的授权条件。
- README.md:87-88 写本项目 MIT，并写明 Linkding 同为 MIT、归因见 UPSTREAM.md。
- UPSTREAM.md:5-8 写上游 `https://github.com/sissbruecker/linkding`、license MIT、attribution `Copyright (c) 2019 Sascha Ißbrücker`。app.py:1-4 写 clean-room、inspired by Linkding (MIT)。自身版权在 LICENSE，上游版权在 UPSTREAM，这种拆法与「独立重写」的说法一致。

不自洽的一处：UPSTREAM.md:21 让读者去看 README 的「与 Linkding 的关系」。README.md 的标题只有「功能清单」「安装与启动」「测试」「后续可扩展项」「许可证」，没有这一节。

未核实，因此不改 LICENSE / UPSTREAM：`source_commit` `27b7303baf41bb28babc610ac8eaa486e1ddfab5`、UPSTREAM.md:12-16 的提交说明与 2026-09-13、以及 UPSTREAM.md:17-18「版权行逐字复制自上游 LICENSE.txt」。本次按任务不访问 GitHub。代码里的 `linkding:bookmarks.archived` 和 `[linkding-notes]`（app.py:32、697-700、798-803）是导入导出格式标记，不能据此认定复制了上游源码；也没有和上游文件做 diff。

## 分级修复清单

### P0

无。安装、21 项测试、8000 首页与健康检查、8123 自测都已跑通。

### P1

1. P1-1 数据接口不执行「必须先改密」。文件：app.py:211-227；使用该依赖的数据接口在 app.py:395、468、510、553、562、601、614、774、821。修法：登录、`/api/me`、改密、退出仍只用 `current_user`；其余数据接口在 `must_change_password` 为真时返回 403。本次修。

2. P1-2 默认监听所有网卡，同时登录页写出默认口令。文件：app.py:847；口令明文在 static/index.html:66（与 README.md:43 一致，不改这句文案）。修法：`uvicorn.run` 的 host 改为环境变量 `HOST`，默认 `127.0.0.1`；在 README.md:47-51 的环境变量表加一行 `HOST`。本次修。

3. P1-3 改密不撤销其他会话。文件：app.py:267-283。探测里 token B 在用 token A 改密之后访问 `/api/me` 仍为 200。修法：改密提交时删掉该用户除当前 token 以外的 `sessions`。本次不改。`tests/test_app.py:31-34` 的模块级 token 在 `test_change_password`（test_app.py:55-70）里先被用来改密，随后另一个 token 把密码改回去；第二次若撤销其他会话，后面的用例会 401。测试不许改。

### P2

本次不改。

1. app.py:192 使用已弃用的 `on_event("startup")`。修法：改成 lifespan，里面调用现有 `init_db()`。现在仍能启动。

2. app.py:94-95 超过 64 字符的标签直接丢掉，接口仍 201。探测：65 个 `x` 未出现在返回的 `tags` 里。NOTES.md:30 写这是对齐 Linkding 的取舍。修法：若要改，对超长标签返回 400，或在响应里列出被丢弃的标签。

3. app.py:478 标题超 512 字静默截断。修法：超长时返回 400，或在响应里标明被截断。

4. app.py:530 把搜索词直接包进 `LIKE %...%`，`%` 和 `_` 仍是通配符。修法：转义这两个字符并加 `ESCAPE`。参数化查询本身有效（探测里引号载荷没有 500）。

5. app.py:34 `FastAPI()` 默认开放 `/docs`。探测 `GET /docs` 为 200。修法：设 `docs_url=None`、`redoc_url=None`、`openapi_url=None`，或加上与数据接口相同的鉴权。

6. app.py:238 用 `!=` 比较密码哈希。修法：改成 `secrets.compare_digest`。

7. static/index.html:70-78 强制改密页没有退出按钮。修法：加一个退出，调用已有的 `/api/logout`。

8. static/index.html:116 搜索占位未写备注。修法：占位补上「备注」。对应 P1 以外的文案，不在本次改。

9. README.md:9、18、71-75 的覆盖率和自测命令与实现不完全一致。修法：按上一节不符项改 README。不在本次改，避免顺手改文案。

10. app.py:354-387 已登录用户可让服务端请求任意 http/https，失败时返回空标题。这是抓取功能本身；test_app.py:243-257 直接对 `127.0.0.1` 调用 `fetch_metadata`。修法：不在本次限制目标地址。
