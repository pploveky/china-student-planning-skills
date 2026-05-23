#!/usr/bin/env python3
"""高考志愿报告用户口吻审计脚本。

用途：
- 扫描最终报告 Markdown，检测开发者口吻、内部文件引用、脚本名和技术元数据泄漏。

核心逻辑：
1. 按行读取报告 Markdown 文本。
2. 使用黑名单正则匹配 SKILL 内部引用、脚本名、HTTP 运维元数据、测试代号等不应交付给用户的内容。
3. 输出命中的行号、类型和片段；发现泄漏时返回非零退出码。

输入输出：
- 输入：报告 Markdown 文件路径。
- 输出：PASS/FAIL 结果与泄漏清单；无泄漏返回 0，有泄漏返回 1。

关键依赖：
- Python 3.10+
- 标准库 re、sys、pathlib

最小使用示例：
    python3 audit_user_voice.py output/report.md
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

# 黑名单：在用户报告 .md 中出现即视为泄漏
BLACKLIST: list[tuple[str, str]] = [
    (r"SKILL(?:\.md)?", "SKILL 内部引用"),
    (r"audit_urls|md_to_pdf|parse_students|gen_test_dataset", "脚本名"),
    (r"HTTP\s?实测|HTTP\s?[234]\d{2}|curl\s?实测", "HTTP 运维元数据"),
    (r"pypdf|matplotlib|网页读取|NXDOMAIN", "技术工具名"),
    (r"硬约束|必读|强制要求|二次核验|二次确认|\[已核 bjeea PDF\]", "内部规约词"),
    (r"\bR_[sur]\b|R_u\s?/\s?R_s|R_s\s?/\s?R_u", "内部数学符号"),
    (r"已升级|已修订|已观测|已被实证|已纳入(?!.*推免)", "演进性表述"),
    (r"BJ-01|HA-02|S\d{2}_", "测试代号"),
    (r"请你直接忽略|当场修正|立即重写", "命令式开发者语"),
    (r"教育部令第\s?\d+\s?号", "法规生硬引用"),
    (r"\b转载页\b", "开发者英文术语 转载页"),
    (r"反爬|UA\s?伪装|限流|412\+网页读取", "运维细节"),
]


def audit(path: Path) -> int:
    if not path.exists():
        print(f"文件不存在: {path}", file=sys.stderr)
        return 1
    text = path.read_text(encoding="utf-8")
    leaks: list[tuple[int, str, str]] = []
    for ln_idx, line in enumerate(text.split("\n"), 1):
        for pat, label in BLACKLIST:
            if re.search(pat, line):
                snippet = line.strip()
                if len(snippet) > 110:
                    snippet = snippet[:110] + "..."
                leaks.append((ln_idx, label, snippet))
                break
    if leaks:
        print(f"FAIL: {path.name} 含 {len(leaks)} 处开发口吻泄漏")
        for ln, label, snippet in leaks:
            print(f"  L{ln} [{label}]: {snippet}")
        print("\n请改写为面向真实考生 + 家长的自然话语。")
        return 1
    print(f"PASS: {path.name} 无开发口吻泄漏")
    return 0


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python audit_user_voice.py <report.md>")
        sys.exit(2)
    sys.exit(audit(Path(sys.argv[1])))


if __name__ == "__main__":
    main()
