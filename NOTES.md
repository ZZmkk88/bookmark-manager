# 开工记录：Linkding 复刻（bookmark-manager）

## 资源核对（动手前）
- Muse 云端实测：CPU 2 核、内存 7.7G、无显卡、Python 3.12.3。
- 本项目方案：Python + FastAPI + SQLite + 单页 HTML，无 Node 构建、无外部服务，
  运行时内存约几十 MB，**带得动**。依赖已装入本地 venv 验证：fastapi 0.156.4 / uvicorn / httpx / pytest。

## 从原项目读到的设计（来源：github.com/sissbruecker/linkding，2026-10-21 逐文件读）
- 定位（README）：自托管书签管理器；核心功能 = 标签组织、自动提供标题/描述/图标、
  Netscape HTML 导入导出、REST API、稍后读（unread）、归档网站快照等。
- 数据模型（bookmarks/models.py）：
  - Bookmark：url(≤2048)、url_normalized（归一化后建索引，专用于判重）、title(≤512)、
    description、notes、unread（稍后读）、is_archived（归档）、shared、date_added/date_modified/date_accessed、owner、tags 多对多。
  - Tag：name(≤64)、date_added、owner。标签名处理：去首尾空格、内部空格换成 `-`、
    按小写去重、按小写排序。标签串以英文逗号分隔。
- 自动抓取（bookmarks/services/website_loader.py）的做法：
  - 流式下载页面，读到 `</head>` 就停（标题和 meta 都在 head 里），上限 5MB，超时 10 秒；
  - 带一套仿浏览器请求头（User-Agent 等）；
  - 标题取 `<title>`；描述先取 `meta[name=description]`，没有再取 `og:description`；
    预览图取 `og:image`，相对地址用 urljoin 补全；
  - 编码不用页面自报的，用 charset_normalizer 猜（很多站点标注不准）；
  - 抓取结果带小缓存（表单预览抓过一次，保存时不重复抓）；任何异常都不抛错，返回空元数据。
- URL 归一化（bookmarks/utils.py normalize_url）：scheme 和域名转小写、路径去尾部斜杠、
  查询参数按名排序、保留 fragment。判重和导入去重都靠它。
- 导入（services/importer.py + parser.py）：
  - 用 HTMLParser 解析 Netscape 格式：`<A>` 的属性 HREF/ADD_DATE/LAST_MODIFIED/TAGS/TOREAD/PRIVATE，
    链接文字是标题，紧跟的 `<DD>` 是描述，描述里用 `[linkding-notes]...[/linkding-notes]` 夹带备注；
  - 归档状态编码成一个伪标签 `linkding:bookmarks.archived` 放在 TAGS 里；
  - 导入按归一化 URL 判重：已存在则更新，不存在则新建；文件内重复也跳过；
    结果统计 total/success/failed；标签超 64 字符跳过；文件夹层级不保留（拍平导入）。
- 导出（services/exporter.py）：标准 Netscape 头 + `<DL><p>`，每条
  `<DT><A HREF ADD_DATE(秒) LAST_MODIFIED PRIVATE TOREAD TAGS>标题</A>` + 可选 `<DD>描述`，
  归档书签把伪标签加回 TAGS；文本做 HTML 转义。
- 搜索（bookmarks/queries.py 与 search_query_parser.py）：原版支持较复杂的查询语法
  （#标签、!未读 等）。MVP 按任务书要求做简化版：关键词匹配标题/网址/描述/备注/标签名 + 独立标签筛选参数。

## 本复刻的取舍（MVP）
- 保留：单用户登录（Token 24h、首次登录提示改密，照 PMC 三阶段做法）、书签增删改查、
  自动抓标题/描述（含 og 兜底、og:title 兜底）、标签（同原版清洗规则）、搜索、
  Netscape 导入/导出（含归档伪标签、备注夹带，与原版互通）、unread、归档开关。
- 简化：编码识别用「响应头 charset → meta charset → utf-8 容错」代替 charset_normalizer；
  抓取上限 1MB（head 足够）；不做 favicon/预览图下载、不做网页快照存档、不做多用户/分享/OIDC/PWA。
- 技术：FastAPI + SQLite（标准库 sqlite3），密码用标准库 pbkdf2_hmac 哈希，
  抓取用标准库 urllib + html.parser（不装 BeautifulSoup），自己重写全部代码，只借鉴上述设计与格式约定。
