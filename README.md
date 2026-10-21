# bookmark-manager · 书签管理器

一个轻量、可自己部署的网页书签管理器：把平时要收藏的网页链接存进来，
自动抓取标题和描述、打标签、全文搜索，还能导入/导出浏览器书签文件。

## 和 Linkding 的关系

本项目是对开源项目 [Linkding](https://github.com/sissbruecker/linkding)（MIT 许可证）
的**复刻学习作品**：借鉴了它的功能设计、数据模型和 Netscape 书签格式约定
（包括归档伪标签 `linkding:bookmarks.archived`、备注夹带 `[linkding-notes]` 的做法，
导出文件可与 Linkding 互通），**代码为独立重写，未复制其源码**。
设计调研细节见 [NOTES.md](NOTES.md)。

和原版的差异（有意做的简化）：单用户使用；不做网站图标/预览图下载、不做网页快照存档、
不做多用户分享与 SSO；界面为单页 HTML。

## 功能清单

- **登录**：单用户账号，Token 登录（24 小时有效），首次登录强制提示改密
- **书签管理**：新增 / 编辑 / 删除 / 列表；只填网址即可保存，标题和描述自动抓取
  （先取网页 `<title>` 和 `meta description`，抓不到再用 Open Graph 的 og:title / og:description 兜底）
- **标签**：多个标签（英文逗号分隔），标签名自动清洗（空格转连字符、忽略大小写去重），点标签即筛选
- **搜索**：关键词匹配标题、网址、描述、备注和标签名
- **稍后读**：unread 标记，可只看稍后读列表
- **归档**：书签可归档，默认列表不显示，在「看归档区」里查看
- **导入**：浏览器导出的书签 HTML 文件（Netscape 格式，Chrome/Firefox/Edge 通用），
  按归一化网址判重（已存在则更新），返回成功/失败统计
- **导出**：一键导出为 Netscape HTML，可再导入任何浏览器或 Linkding

## 怎么运行

需要 Python 3.10+。

```bash
cd bookmark-manager
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py            # 默认监听 8000 端口，可用 PORT 环境变量改
```

打开 http://localhost:8000 ，默认账号 **admin / admin123**，首次登录会要求改密码。

可选环境变量：

| 变量 | 说明 | 默认 |
|---|---|---|
| `PORT` | 监听端口 | 8000 |
| `BOOKMARK_DB_PATH` | SQLite 数据库文件位置 | `data/bookmarks.db` |
| `BM_INITIAL_USERNAME` / `BM_INITIAL_PASSWORD` | 首次启动创建的初始账号 | admin / admin123 |

## 测试

```bash
.venv/bin/pip install httpx pytest
.venv/bin/python -m pytest tests/ -q     # 21 项自动化测试
```

真实数据全流程自测（需先按上面方式启动服务，端口 8123、全新数据库）：

```bash
PORT=8123 .venv/bin/python app.py &
BASE=http://127.0.0.1:8123 .venv/bin/python tests/live_selftest.py
```

## 后续可扩展项

- 浏览器扩展 / 书签小工具（bookmarklet）一键收藏
- favicon 与预览图抓取、网页快照存档（原版 Linkding 有，本复刻暂缺）
- 多用户与书签分享
- 搜索语法增强（`#标签`、`!未读` 等，原版有成熟实现可参考）

## 许可证

MIT。本项目为独立实现；所借鉴的 Linkding 同为 MIT 许可证。
