# bookmark-manager · 书签管理器

一句话定位：一个轻量、可自己部署的网页书签管理器——存链接、自动抓标题和描述、打标签、全文搜索，并能与浏览器互相导入导出书签。

**参考了 Linkding 的设计（思想与格式约定）：**

- 功能范围的划分：书签 + 标签 + 稍后读（unread)+ 归档这套核心概念
- 数据模型字段：网址、归一化网址、标题、描述、备注、未读、归档、添加/修改时间、标签多对多
- 自动抓取的策略：只下载到 `</head>` 为止、仿浏览器请求头、标题取 `<title>`、
  描述先取 meta description、缺失时用 og:description 兜底、抓取失败不报错返回空
- 标签清洗规则：去首尾空格、内部空格换成 `-`、忽略大小写去重、逗号分隔
- URL 归一化规则（判重用）：域名转小写、路径去尾斜杠、查询参数排序
- Netscape 书签文件格式约定：导入按归一化网址判重更新、归档状态用伪标签
  `linkding:bookmarks.archived` 编码、备注用 `[linkding-notes]...[/linkding-notes]` 夹带

**独立实现的部分（代码全部自己写，未复制上游源码）：**

- 全部后端代码：单文件 FastAPI 应用 + SQLite 存储（上游是 Django + ORM）
- 全部前端代码：单个原生 HTML/JS 页面（上游是 Django 模板 + 前端构建）
- 登录与会话：密码用标准库 pbkdf2_hmac 哈希、自研 Token 会话（上游用 Django 账号体系）
- 抓取与解析：只用 Python 标准库 urllib + html.parser（上游用 requests + BeautifulSoup)
- 搜索：SQL LIKE 关键词匹配（上游有独立的查询语法解析器，本项目未实现该语法）

**有意没做的**（原版有、本复刻暂缺）：网站图标与预览图、网页快照存档、多用户与分享、
SSO/OIDC、PWA、浏览器扩展。

## 功能清单（与代码实现一一对应，均已测试覆盖）

- **登录**：单用户账号，Token 登录（24 小时有效），首次登录强制提示改密
- **书签管理**：新增 / 编辑 / 删除 / 列表；只填网址即可保存，标题和描述自动抓取
  （先取网页 `<title>` 和 `meta description`，抓不到再用 Open Graph 的 og:title / og:description 兜底；重复网址会按归一化结果判重并拒绝）
- **标签**：多个标签（英文逗号分隔），标签名自动清洗（空格转连字符、忽略大小写去重），点标签即筛选
- **搜索**：关键词匹配标题、网址、描述、备注和标签名
- **稍后读**：unread 标记，可只看稍后读列表
- **归档**：书签可归档，默认列表不显示，在「看归档区」里查看
- **导入**：浏览器导出的书签 HTML 文件（Netscape 格式，Chrome/Firefox/Edge 通用），
  按归一化网址判重（已存在则更新，文件内重复跳过），返回总数/成功/失败统计
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
| `BOOKMARK_DB_PATH` | SQLite 数据库文件位置 | `data/bookmarks.db` |
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
- 搜索语法增强（`#标签`、`!未读` 等，原版有成熟实现可参考）

## 许可证

MIT（见 [LICENSE](LICENSE)）。本项目为独立实现；所借鉴的 Linkding 同为 MIT 许可证，
其版权归因见 [UPSTREAM.md](UPSTREAM.md)。
