# bookmark-manager 验收报告

## 结论

**能在本地跑起来。**

- `python -m pytest -q`：退出码 0，`21 passed, 3 warnings in 4.13s`，没有失败。
- `python -c "import app"`：退出码 0，加载的是本仓库 `app.py`。
- 以 `__main__` 执行 `app.py` 后，Uvicorn 监听 `http://0.0.0.0:18765`。本机 `GET /health` 返回 200，`GET /` 返回 200，登录返回 200。随即停掉；再请求 `/health` 不再返回 200。

跑得起来，不代表文档和许可证过关。下面 5 处说法大于实现，MIT 上游版权声明也不在仓库里。没有阻断级的启动故障。

本次没有改仓库源码。`tests/live_selftest.py` 会请求 `https://docs.python.org/3/`（该文件第 115–118 行），按任务禁止外网，没有跑。这不算项目缺陷。

## 1. pytest

工作目录 `E:\muse-bridge\in\TASK-001-bookmark-manager`。解释器 `E:\muse-bridge\env\bookmark-manager\Scripts\python.exe`，Python 3.11.9。

命令：`python -m pytest -q`  
退出码：0

```text
.....................                                                    [100%]
============================== warnings summary ===============================
app.py:192
  E:\muse-bridge\in\TASK-001-bookmark-manager\app.py:192: DeprecationWarning: 
          on_event is deprecated, use lifespan event handlers instead.
  
          Read more about it in the
          [FastAPI docs for Lifespan Events](https://fastapi.tiangolo.com/advanced/events/).
          
    @app.on_event("startup")

..\..\env\bookmark-manager\Lib\site-packages\fastapi\applications.py:4723
  E:\muse-bridge\env\bookmark-manager\Lib\site-packages\fastapi\applications.py:4723: DeprecationWarning: 
          on_event is deprecated, use lifespan event handlers instead.
  
          Read more about it in the
          [FastAPI docs for Lifespan Events](https://fastapi.tiangolo.com/advanced/events/).
          
    return self.router.on_event(event_type)  # ty: ignore[deprecated]

..\..\env\bookmark-manager\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\env\bookmark-manager\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
21 passed, 3 warnings in 4.13s
```

21 个点与 README.md:55「21 项自动化测试」一致。3 条都是警告：`app.py:192` 的 `@app.on_event("startup")` 已弃用；另外两条来自当前环境里的 FastAPI/Starlette（`starlette-1.9.0.dist-info`）配 `httpx 0.28.1`。警告没有让用例失败。

本机已装版本（命令输出）：fastapi `0.153.0`，uvicorn `0.54.0`，httpx `0.28.1`，pytest `9.1.1`。`python_multipart-0.0.32.dist-info\METADATA` 中 `Version: 0.0.32`。

## 2. 应用是否能起来

导入：

```text
E:\muse-bridge\env\bookmark-manager\Scripts\python.exe
3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
IMPORT_OK E:\muse-bridge\in\TASK-001-bookmark-manager\app.py bookmark-manager
```

`$env:PORT=...; python app.py` 被本会话的权限检查拦住，**没有执行**，不能写成已用这条命令验证。

实际启动方式：在同一进程里设置 `PORT=18765`、`BOOKMARK_DB_PATH` 指向 `C:\Users\xzm\AppData\Local\Temp\bm-acc-task001\live.db`，再 `runpy.run_path(app.py, run_name="__main__")`。这会执行 `app.py:844-847` 的 `uvicorn.run(app, host="0.0.0.0", port=...)`。

```text
INFO:     Started server process [20980]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:18765 (Press CTRL+C to quit)
```

本机 httpx：

```text
HEALTH 200 {"ok":true,"app":"bookmark-manager"}
INDEX 200 15183 True
UNAUTH 401
LOGIN 200 True 43
LIST 200 {"bookmarks":[],"total":0}
DOCS 200
```

对应关系：`/health` 为 `app.py:839-841`；页面 15183 字节且含默认口令，与 `static/index.html:66` 一致；未登录列表 401，与 `app.py:211-214` 一致；`admin/admin123` 登录成功且 `must_change_password` 为真，与 `app.py:27-28`、`app.py:184` 一致；未改密时列表仍是 200；未带令牌的 `GET /docs` 也是 200（`app.py:34` 使用 FastAPI 默认文档）。

停掉后台任务后，工具返回 `killed: Task was terminated successfully`。再请求 `http://127.0.0.1:18765/health`（timeout 2 秒）退出码 1，异常 `httpx.ConnectTimeout`。`Test-Path` 仓库下的 `data` 为 `False`。临时库留在 `%TEMP%\bm-acc-task001\`，未删除。

## 3. 文档与实现（5 处）

核对后与代码一致、这里不展开的包括：Token 有效期 24 小时（`app.py:26`）、默认账号（`app.py:27-28`）、`BOOKMARK_DB_PATH`（`app.py:25`）、归档伪标签与 `[linkding-notes]`（`app.py:32`、`app.py:697-701`、`app.py:798-803`）、抓取上限 1MB（`app.py:309`）、标题用 `<title>` 否则 `og:title`、描述用 `meta description` 否则 `og:description`（`app.py:381-382`）。NOTES.md:8-36 对上游仓库的逐文件转述本次没有联网核对，**未核实**，不记成缺陷，也不记成已证实。README.md:11「未复制其源码」同样未做逐行对照，**未核实**。

1. **「全文搜索」大于实现。** README.md:4 写全文搜索。列表查询是 `LIKE '%关键词%'`（`app.py:528-534`），没有 FTS 表。功能清单 README.md:23 写的「关键词匹配标题、网址、描述、备注和标签名」与这句 SQL 一致，开篇那句偏大。另外 `%`、`_` 会变成通配符：临时库里 3 条书签都不含字面量 `%`，`q=%` 仍返回 3，`q=e%d` 返回 2，`q=nomatchzzz` 返回 0。

2. **「与 Linkding / 任何浏览器互通」没有对照实验。** README.md:11、README.md:28、NOTES.md:40 都这么写。仓库里的证据只是把自己导出的 HTML 再导入自己（`tests/test_app.py:302-324`，且包含在已通过的 21 项里）。导出是一层 `<DL>`（`app.py:788-814`），不写文件夹。NOTES.md:30 自己也写了文件夹会拍平。

3. **「首次登录强制改密」只挡页面。** README.md:19、README.md:41。页面在 `static/index.html:161` 会停在改密视图。服务端 `current_user`（`app.py:211-225`）不看 `must_change_password`。两处实测都是未改密就 `GET /api/bookmarks` → 200：TestClient，以及上面的 uvicorn `LIST 200`。改密只更新 `users`（`app.py:276-280`），不删 `sessions`。TestClient 上改密后原 token 访问 `/api/me` 仍是 200，`sessions` 行数仍是 1。

4. **导入「已存在则更新」没写文件内重复。** README.md:27。库里已经有的归一化 URL 会更新（`app.py:744-752`）。同一个文件里第二条相同 URL 直接计失败并 `continue`（`app.py:733-735`），不会覆盖第一条。实测导入 `https://example.com/dup` 与带尾斜杠的同一条：`{"total":2,"success":1,"failed":1}`，留下的标题是 `One`，不是第二条的 `Two`。NOTES.md:29「文件内重复也跳过」与代码一致，README 这句不完整。

5. **文档写 localhost，进程听 0.0.0.0。** README.md:38-41 让人打开 `http://localhost:8000`。`app.py:847` 是 `host="0.0.0.0"`。本次日志原文是 `Uvicorn running on http://0.0.0.0:18765`。默认口令 `admin/admin123` 写在 README.md:41 和 `static/index.html:66`，并且接口不强制改密（见第 3 条）。局域网可以在改密之前用这对口令拿 Token。

另有一处数字对不上本机，但不算功能缺陷：NOTES.md:6 写已验证 fastapi `0.156.4`。本机这个 venv 的 `fastapi.__version__` 是 `0.153.0`。NOTES.md:4 的云端 Python 3.12.3 也与本机 3.11.9 不同。内存「几十 MB」本次没有测量，**未核实**。

## 4. LICENSE 与 Linkding 署名

`LICENSE:3` 只有：

```text
Copyright (c) 2026 bookmark-manager contributors
```

全文是一份完整 MIT（`LICENSE:1-21`），约束的是**这份新代码**。仓库的 `.py/.md/.html/.txt` 里能检索到 Linkding 的项目名、GitHub 链接和「MIT」三个字（README.md:8-11、README.md:74，NOTES.md:8，`app.py:3`），**没有**上游版权人、年份，也没有上游许可全文。无扩展名的 `LICENSE` 已整份读过，同样没有。

上游版权人姓名和年份：本次禁止联网，仓库里也没有原文，**未核实**。不要凭记忆补进 LICENSE。

按本次验收要求的「保留原始版权声明与出处」，**当前不满足**。MIT 原文的义务是：再分发该软件或其重要部分时，必须带上**该软件**的版权声明和许可全文。独立重写并不自动触发这句。README 声称独立重写，本次又没有和上游逐行比对，所以不能写成「已经构成违反 MIT」，也不能写成「署名已经合规」。

## 5. 修复清单

### 阻断

无。测试 21 项通过，导入与短时 Uvicorn 都成功。

### 严重

1. **未改密即可调用业务接口，改密也不废除旧 Token。**  
   位置：`app.py:211-225`，`app.py:276-280`。  
   改法：在 `current_user` 取出用户后增加：若 `user["must_change_password"]` 为真，且 `request.url.path` 不是 `/api/change-password`、`/api/logout`、`/api/me`，则 `raise HTTPException(status_code=403, detail="请先修改密码")`。  
   `change_password` 在更新密码并 `commit` 之前执行 `DELETE FROM sessions WHERE user_id = ?`，再 `secrets.token_urlsafe(32)` 插入一条新会话，返回 `{"ok": true, "token": new_token}`。`static/index.html:182-189` 收到 `data.token` 时写回 `localStorage` 的 `bm_token`，再调用 `boot()`。这样改密前发出的 Token（包括仍是默认口令时发出的）会失效。

2. **默认口令配上全网卡监听。**  
   位置：`app.py:847`；口令默认值在 `app.py:27-28`。  
   改法：`uvicorn.run` 改为 `host=os.environ.get("HOST", "127.0.0.1")`，端口仍用 `PORT`。README.md 的环境变量表加上 `HOST`，默认 `127.0.0.1`。需要给局域网用时再显式设置 `HOST=0.0.0.0`。

3. **LICENSE 没有上游版权声明。**  
   位置：`LICENSE:3`；致谢只到 README.md:8-11 与 README.md:74。  
   改法：在 `LICENSE` 末尾加一节 NOTICE，写明本作品为独立实现，Netscape 归档伪标签 `linkding:bookmarks.archived` 与 `[linkding-notes]` 约定来自 Linkding（MIT），并给出 `https://github.com/sissbruecker/linkding`。上游版权行从该仓库 `LICENSE` **原样复制**（本报告未核实该行全文，不要手写一个记得的名字）。若事后发现某个文件复制了上游的实质代码，把上游 MIT 全文和版权行放进该文件或 NOTICE。README.md:11 在完成对照之前，应避免写成已经证明「未复制源码」。

### 一般

1. **全文搜索措辞，以及 LIKE 通配符。**  
   位置：README.md:4；`app.py:528-534`。  
   改法：README 改成「关键词搜索」。查询改为先转义再绑定，并为每个 `LIKE` 加上 `ESCAPE '\'`：

```python
escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
like = f"%{escaped}%"
where.append(
    "(b.title LIKE ? ESCAPE '\\' OR b.url LIKE ? ESCAPE '\\' "
    "OR b.description LIKE ? ESCAPE '\\' OR b.notes LIKE ? ESCAPE '\\' "
    "OR tq.name LIKE ? ESCAPE '\\')"
)
```

2. **互通说法收窄。**  
   位置：README.md:11、README.md:28、NOTES.md:40。  
   改法：改成「导出使用 Linkding 的归档伪标签和备注标记；本仓库只验证了再导入自己。导出是单层列表，不保留浏览器文件夹。尚未用 Linkding 或 Chrome/Firefox/Edge 的真实导出文件做对照。」

3. **导入统计与 README 对齐。**  
   位置：README.md:27；行为在 `app.py:733-735`。  
   改法：README 补上「同一文件内重复的归一化网址计为 failed，不覆盖文件中先出现的那条；数据库里已有的网址才更新」。代码可保持现状，与 NOTES.md:29 已经一致。

4. **填了标题就完全不抓描述。**  
   位置：`app.py:473-477`。实测：title 为 `kept`、description 为空时 `fetch_metadata` 调用 0 次，描述仍为空；只提交 URL 时调用 1 次。  
   改法：二选一。要么 README.md:20 写成「仅当标题为空时才抓取；此时才顺带填描述」。要么把条件改成 `if not title or not description:`，在分支里只填仍然为空的字段，避免标题已有时把描述留空。

5. **启动事件弃用警告。**  
   位置：`app.py:34` 与 `app.py:192-194`。pytest 和 Uvicorn 日志都打出了这条 DeprecationWarning。  
   改法：删掉 `@app.on_event("startup")`。把 `app = FastAPI(...)` 挪到 `init_db` 定义之后、第一个 `@app.post` 之前，改为：

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield

app = FastAPI(title="bookmark-manager", lifespan=lifespan)
```

   `login` 里 `app.py:232` 的 `init_db()` 可以留着，重复执行是 `CREATE TABLE IF NOT EXISTS`。

6. **搜索框没写备注，接口会搜备注。**  
   位置：`static/index.html:116`；SQL 在 `app.py:532` 含 `b.notes`。  
   改法：placeholder 改为「搜索标题 / 网址 / 描述 / 备注 / 标签」。

7. **版本号与本机 venv 不一致。**  
   位置：NOTES.md:6。  
   改法：改成「依赖见 requirements.txt」。若要写版本，写本次环境的 fastapi 0.153.0 / uvicorn 0.54.0 / httpx 0.28.1 / pytest 9.1.1，或注明 0.156.4 只属于另一台机器。

8. **OpenAPI 文档无需登录。**  
   位置：`app.py:34`。实测未授权 `GET /docs` 为 200。  
   改法：`FastAPI(..., docs_url=None, redoc_url=None, openapi_url=None)`，或给文档路由加上与 `current_user` 相同的依赖。

9. **运行说明只有 Unix 路径。**  
   位置：README.md:36-38、README.md:55。  
   改法：补上 Windows：`py -m venv .venv`，然后 `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`，再 `.\.venv\Scripts\python.exe app.py`。测试同样换成 `.\.venv\Scripts\python.exe -m pytest tests\ -q`。本次验收用的是 PATH 里的 python，不是 README 里的 `.venv/bin/python`。

10. **测试共用一个模块级数据库，顺序绑在一起。**  
    位置：`tests/test_app.py:10-16`、`tests/test_app.py:19-34`。这次整包跑是通过的。  
    改法：用 pytest 的 `tmp_path` 做函数级或模块级 fixture，在导入 `app` 之前设置 `BOOKMARK_DB_PATH`，避免 `test_change_password` 中途失败后把后续用例的口令弄乱。
