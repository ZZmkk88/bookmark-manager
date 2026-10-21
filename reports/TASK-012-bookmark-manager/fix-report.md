# bookmark-manager 修复记录

只改 review.md 清单里的 P1-1、P1-2。P1-3 不改，原因见文末。测试文件未改。

## P1-1 数据接口在未改密时拒绝

问题：`must_change_password` 只影响前端。审查时 `current_user`（当时 app.py:211-227）不看这个标志，未改密也能调用书签接口。

文件：`app.py`。新增 `require_changed_password`（现 app.py:230-234）。下列数据接口的依赖从 `current_user` 改为 `require_changed_password`（行号为改后）：app.py:402、475、517、560、569、608、621、781、828。`/api/login`、`/api/me`（app.py:294）、`/api/change-password`（app.py:275）、`/api/logout`（app.py:263）仍只用 `current_user`。

改法：已登录但 `must_change_password` 为真时，数据接口返回 403，`detail` 为「请先修改密码」。

验证命令：

```
Set-Location E:\muse-bridge\in\TASK-012-bookmark-manager
E:\muse-bridge\work\TASK-012-bookmark-manager\.venv\Scripts\python.exe -m pytest tests/ -q --tb=short
E:\muse-bridge\work\TASK-012-bookmark-manager\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-012-bookmark-manager\probe_p11.py
```

pytest 输出：

```
21 passed, 3 warnings in 4.29s
```

退出码 0。警告仍是 `on_event` 弃用和 Starlette/httpx TestClient 弃用，与改前相同。

probe_p11.py 输出：

```
LOGIN 200 {"token":"...","username":"admin","must_change_password":true}
BOOKMARKS_BEFORE 403 {"detail":"请先修改密码"}
ME_BEFORE 200 {"username":"admin","must_change_password":true}
LOGOUT 200 {"ok":true}
CHANGE 200 {"ok":true}
BOOKMARKS_AFTER 200 {"bookmarks":[],"total":0}
NOAUTH 401
```

未改密时列表 403；`/api/me` 与退出仍可用；改密后列表 200；无 token 仍是 401。
