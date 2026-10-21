# bookmark-manager · 书签管理器

一句话定位：一个轻量、可自己部署的网页书签管理器——存链接、自动抓标题和描述、打标签、全文搜索，并能与浏览器互相导入导出书签。

本项目的设计学习了开源社区书签管理工具的通行思路——如标签、归档、稍后读这类核心概念，
以及浏览器书签导入导出的通用格式约定；代码为独立实现。上游溯源与署名见 [UPSTREAM.md](UPSTREAM.md)。

## 功能清单（与代码实现一一对应，均已测试覆盖）

- **登录**：单用户账号，Token 登录（24 小时有效），首次登录强制提示改密
- **书签管理**：新增 / 编辑 / 删除 / 列表；只填网址即可保存，标题和描述自动抓取
  （先取网页 `<title>` 和 `meta description`，抓不到再用 Open Graph 的 og:title / og:description 兜底；重复网址会按归一化结果判重并拒绝）
- **标签**：多个标签（英文逗号分隔），标签名自动清洗（空格转连字符、忽略大小写去重），点标签即筛选
- **搜索**：关键词匹配标题、网址、描述、备注和标签名
- **稍后读**：unread 标记，可只看稍后读列表
- **归档**：书签可归档，默认列表不显示，在「看归档区」里查看
- **导入**：浏览器导出的书签 HTML 文件（Netscape 格式，Chrome/Firefox/Edge 通用），
  按归一化网址判重（已存在则更新），返回总数/成功/失败/跳过统计——
  同一文件内出现两次的网址计入「跳过」而非失败
- **导出**：一键导出为 Netscape HTML，可再导入任何浏览器或 Linkding

## 安装与启动

需要 Python 3.10 或更高版本。

**Linux / macOS（bash）:**

```bash
cd bookmark-manager
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py            # 默认监听 8000 端口
```

**Windows（PowerShell）:**

```powershell
cd bookmark-manager
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python app.py        # 默认监听 8000 端口
```

启动后打开 http://localhost:8000 ，默认账号 **admin / admin123**，首次登录会要求改密码。

可选环境变量：

| 变量 | 说明 | 默认 |
|---|---|---|
| `PORT` | 监听端口（Windows PowerShell 里用 `$env:PORT=8123` 设置） | 8000 |
| `BM_HOST` | 监听地址。默认 `127.0.0.1`（仅本机可访问）；设为 `0.0.0.0` 可让局域网访问，**请务必先改掉默认密码** | 127.0.0.1 |
| `BOOKMARK_DB_PATH` | SQLite 数据库文件位置；默认值是 app.py 所在目录下的 `data/bookmarks.db`（不跟随启动时的当前目录走） | `data/bookmarks.db` |
| `BM_INITIAL_USERNAME` / `BM_INITIAL_PASSWORD` | 首次启动创建的初始账号 | admin / admin123 |

## 测试

先装测试依赖（两个系统的命令只是路径写法不同）：

```bash
# Linux / macOS
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests/ -q
```

```powershell
# Windows (PowerShell)
.venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest tests/ -q
```

共 21 项自动化测试（登录/改密、增删改查、自动抓取、标签、搜索、导入去重、导出往返、Token 过期）。

真实数据全流程自测（需先以 8123 端口、全新数据库启动服务，两个系统同理，把路径换成对应写法）：

```bash
PORT=8123 .venv/bin/python app.py &
BASE=http://127.0.0.1:8123 .venv/bin/python tests/live_selftest.py
```

## 后续可扩展项

- 浏览器扩展 / 书签小工具（bookmarklet）一键收藏
- favicon 与预览图抓取、网页快照存档
- 多用户与书签分享
- 搜索语法增强（`#标签`、`!未读` 等）

## 许可证

MIT（见 [LICENSE](LICENSE)）。本项目为独立实现；所借鉴的 Linkding 同为 MIT 许可证，
其版权归因见 [UPSTREAM.md](UPSTREAM.md)。
