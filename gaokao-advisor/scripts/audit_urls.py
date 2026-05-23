#!/usr/bin/env python3
"""高考志愿报告脚注 URL 直达性审计脚本。

用途：
- 扫描报告 Markdown 中的脚注 URL，检查是否为可访问的深链接，避免只给首页或失效链接。

核心逻辑：
1. 解析 Markdown 脚注，兼容裸 URL 与 [锚文本](url) 两种格式。
2. 识别裸域名、首页文件等浅链接，并用 curl 获取 HTTP 状态码。
3. 统计浅链接和异常状态码；发现问题时返回非零退出码。

输入输出：
- 输入：报告 Markdown 文件路径。
- 输出：逐条脚注的 HTTP 状态、深链判断和 URL；全部通过返回 0，否则返回 1。

关键依赖：
- Python 3.10+
- curl 命令行工具

最小使用示例：
    python3 audit_urls.py output/report.md
"""
from __future__ import annotations
import re
import subprocess
import sys
from pathlib import Path

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# 不算"深链"的尾巴：URL 末尾是裸域名 或 域名/，没有路径段或文件
SHALLOW_PATTERNS = [
    re.compile(r"^https?://[a-zA-Z0-9\.\-]+/?$"),   # 裸域名
    re.compile(r"^https?://[a-zA-Z0-9\.\-]+/index\.(html?|do|jsp|asp)$"),  # 首页文件
]


def is_shallow(url: str) -> bool:
    return any(p.match(url) for p in SHALLOW_PATTERNS)


def http_code(url: str, timeout: int = 10) -> str:
    try:
        r = subprocess.run(
            ["curl", "-sLo", "/dev/null", "-w", "%{http_code}",
             "-m", str(timeout), "-A", UA, url],
            capture_output=True, text=True, timeout=timeout + 3,
        )
        return r.stdout.strip() or "ERR"
    except Exception:
        return "ERR"


def parse_footnotes(text: str) -> list[tuple[str, str, str]]:
    """返回 [(footnote_id, full_text, first_url)]。

    支持两种 URL 出现形式：
    1. 裸 URL：https://example.com/path
    2. Markdown 锚文本：[锚文本](https://example.com/path)
    """
    pat = re.compile(r"^\[\^([^\]]+)\]:\s*(.+?)(?=^\[\^|\Z)", re.M | re.S)
    # 优先匹配 markdown 锚文本格式 [text](url)，回退到裸 URL
    md_link_pat = re.compile(r"\[[^\]]+?\]\((https?://[^)\s]+)\)")
    bare_pat = re.compile(r"https?://[^\s\)\]\>，。、\"]+")
    out = []
    for m in pat.finditer(text):
        fid, body = m.group(1), m.group(2).strip()
        url_m = md_link_pat.search(body)
        if url_m:
            url = url_m.group(1).rstrip(".)，。")
        else:
            url_m = bare_pat.search(body)
            url = url_m.group(0).rstrip(".)，。") if url_m else ""
        out.append((fid, body, url))
    return out


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    md = Path(sys.argv[1])
    text = md.read_text(encoding="utf-8")
    footnotes = parse_footnotes(text)
    if not footnotes:
        print("未找到脚注")
        return

    print(f"{'fid':<6} {'http':<6} {'deep':<5} URL")
    print("-" * 100)
    shallow_cnt = 0
    bad_http_cnt = 0
    for fid, body, url in footnotes:
        if not url:
            print(f"[^{fid}]  -      -     <无 URL>  {body[:60]}")
            continue
        deep = "no" if is_shallow(url) else "yes"
        if deep == "no":
            shallow_cnt += 1
        code = http_code(url)
        if code not in ("200", "302", "412"):
            bad_http_cnt += 1
        print(f"[^{fid}]  {code:<6} {deep:<5} {url}")
    print("-" * 100)
    total = len(footnotes)
    print(f"总计 {total} 条脚注；"
          f"裸首页 URL: {shallow_cnt}；"
          f"HTTP 异常: {bad_http_cnt}")
    if shallow_cnt or bad_http_cnt:
        print("FAIL：违反 SKILL.md '脚注 URL 直达性硬约束'，必须修正后再交付。")
        sys.exit(1)
    print("PASS：全部脚注 URL 直达且可达。")


if __name__ == "__main__":
    main()
