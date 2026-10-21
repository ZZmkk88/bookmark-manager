# bookmark-manager 修复记录

只修 review.md 清单里的 P0。P1 清单为空，没有修。P2 未动。

## P0-1 跳过改密后调用了不存在的 loadAll

- 问题编号：P0-1
- 文件:行号：`static/index.html:208`（修复前这一行）
- 改法：把 `loadAll()` 改成同文件已有的 `refresh()`（`static/index.html:267`）。`loadAll` 在仓库里没有定义，点击「稍后再说，先用着」会抛 ReferenceError，书签列表和标签不会加载。`refresh` 会调用 `loadTags` 和 `loadList`。
- 未改：`static/index.html:66` 的「会要求改密码」文案（P2-1），测试文件，依赖版本，LICENSE，UPSTREAM。

验证命令（仓库目录 `E:\muse-bridge\in\TASK-019-bookmark-manager`）：

```
E:\muse-bridge\work\TASK-019-bookmark-manager\.venv\Scripts\python.exe -m pytest tests/ -q
```

真实输出（exit 0）：

```
.............................                                            [100%]
29 passed in 15.94s
```

没有失败项。

源码核对：`static/index.html:208` 现为 `$("skipChangeBtn").onclick = () => { show("appView"); refresh(); };`，`static/index.html:267` 仍是 `async function refresh()`。全文件已无 `loadAll`。没有浏览器工具，没有在浏览器里点击「稍后再说」。pytest 不覆盖这段前端脚本，所以全绿只说明后端测试没有被这次改动弄坏。

`git diff -- static/index.html` 只有这一行替换：`loadAll()` → `refresh()`。

## 修完后的全量测试

同上一次 pytest，29 passed in 15.94s，exit 0。没有仍然失败的测试。

## git status --porcelain

命令在仓库目录执行：

```
git status --porcelain
```

输出原文：

```
 M static/index.html
```

工作区里仍有这一处修改，没有被还原。
