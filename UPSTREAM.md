# 上游溯源（UPSTREAM）

本项目是对开源项目 Linkding 的复刻学习作品。按接力规范记录上游信息如下：

- **source_url**: https://github.com/sissbruecker/linkding
- **source_commit**: 27b7303baf41bb28babc610ac8eaa486e1ddfab5
- **license**: MIT
- **attribution**: Copyright (c) 2019 Sascha Ißbrücker

## 说明

- `source_commit` 是 2026-10-21 通过 GitHub 接口实查的上游默认分支 HEAD 提交
  （提交说明 "Update CHANGELOG.md"，提交时间 2026-09-13）；当日做设计调研时通读的
  上游源码正是这一提交，包括 README、bookmarks/models.py、
  bookmarks/services/website_loader.py、importer.py、exporter.py、parser.py、
  bookmarks/utils.py。
- `attribution` 的版权行逐字复制自上游仓库 `LICENSE.txt` 原文第一行版权声明，
  未做任何改动（上游许可证标题为 "The MIT License (MIT)"）。
- 本项目代码为独立重写，未复制上游源码；借鉴的是功能设计、数据模型、
  抓取策略、标签规则与 Netscape 书签格式约定，具体对照见 README 的
  「与 Linkding 的关系」一节和 NOTES.md 的调研笔记。
