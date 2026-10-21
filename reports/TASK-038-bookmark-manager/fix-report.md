# 修复记录

只处理 review.md 里的 P0/P1。P0 没有。P1 有 2 条，改了 1 条，另 1 条修不动。

## P1-1 非规范 IPv4 绕过抓取守卫

- 问题编号：P1-1
- 文件：`app.py:396-411` 新增 `_coerce_ip_literal`；`app.py:421-424` 在 DNS 之前先走它。原先放行逻辑在改前的 `app.py:403-411`。
- 改法：`ipaddress` 不认识的主机名，若不含冒号，再用 `socket.inet_aton` 收成规范 IPv4。收得出来就交给 `_is_public_ip`。这样十进制 `2852039166`（169.254.169.254）、`2130706433`（127.0.0.1）、十六进制、八进制和 `127.1` 会拒绝并带上「拒绝抓取」。`evil.example` / `public.example` 这种主机名 `inet_aton` 会拒绝，仍走原来的 DNS 路径。公网字面量 `8.8.8.8` 仍放行。

验证命令与结果：

```
E:\muse-bridge\work\TASK-038-bookmark-manager\.venv\Scripts\python.exe -m pytest tests\test_app.py -q --tb=short -k ssrf
....                                                                     [100%]
4 passed, 39 deselected in 1.87s
```

exit 0。

同一次改动后的本地探针（`probe_after.py`，未打桩，不解析外网名字）：

```
BLOCKED  http://2130706433/ :: 拒绝抓取内网/保留地址：2130706433（127.0.0.1）
BLOCKED  http://2852039166/ :: 拒绝抓取内网/保留地址：2852039166（169.254.169.254）
BLOCKED  http://0x7f000001/ :: 拒绝抓取内网/保留地址：0x7f000001（127.0.0.1）
BLOCKED  http://0xa9fea9fe/ :: 拒绝抓取内网/保留地址：0xa9fea9fe（169.254.169.254）
BLOCKED  http://0177.0.0.1/ :: 拒绝抓取内网/保留地址：0177.0.0.1（127.0.0.1）
BLOCKED  http://127.1/ :: 拒绝抓取内网/保留地址：127.1（127.0.0.1）
BLOCKED  http://0/ :: 拒绝抓取内网/保留地址：0（0.0.0.0）
BLOCKED  http://127.0.0.1/
BLOCKED  http://localhost/
BLOCKED  http://[::1]/
ALLOWED  http://8.8.8.8/
ALLOWED  http://1.2.3.4/
```

## P1-2 校验地址没有钉死到实际连接

- 问题编号：P1-2
- 文件：`app.py:445-453` 的 `_open_with_redirect_guard`（`app.py:453` 的 `_FETCH_OPENER.open` 再次解析）。改前行号是 `app.py:426-434`。
- 改法：未改。
- 修不动的原因：`tests/test_app.py:662-689` 的 `test_ssrf_public_allowed_and_redirect_hops_checked` 把 `resolve_host_addresses` 固定成公网 `93.184.216.34`，把 `socket.getaddrinfo` 指到本机测试端口的 `127.0.0.1`，并断言页面能抓到。守卫和真实连接必须看到不同地址，这个测试才会绿。把连接钉死在已校验 IP 上，这个测试会去连 `93.184.216.34` 或在连接前把 `127.0.0.1` 判为拒绝，两种都会失败。任务禁止改测试、禁止改断言。

## 全量测试

改完 P1-1 后重跑（cwd = 仓库，`python -m pytest tests -q --tb=line`）：

```
...........................................                              [100%]
43 passed in 19.69s
```

exit 0。没有失败项。

## git status --porcelain

```
git status --porcelain
 M app.py
```
