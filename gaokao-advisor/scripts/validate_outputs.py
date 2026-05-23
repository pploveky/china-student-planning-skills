#!/usr/bin/env python3
"""高考志愿交付物校验脚本。

用途：
- 检查高考志愿规划交付物是否满足发布级硬门禁。

核心逻辑：
1. 使用 PyMuPDF 读取主报告、志愿卡片和应急卡片 PDF 的文本与页数。
2. 从 Markdown 源文件中统计志愿表填写顺序卡片是否按本省填报位完整展开。
3. 检查主报告必须章节、学生姓名、数据来源、免责声明和禁止出现的内部痕迹。
4. 任一硬性门禁失败即返回非零退出码。

输入输出：
- 输入：主报告 PDF、志愿表 PDF、Markdown 源、应急一页纸 PDF、学生姓名和预期志愿位数量。
- 输出：终端校验摘要；成功返回 0，失败返回 1，依赖缺失返回 2。

关键依赖：
- Python 3.10+
- PyMuPDF（fitz）

最小使用示例：
    python3 validate_outputs.py --report report.pdf --card card.pdf --source-md report.md --emergency emergency.pdf --student-name 张同学 --expected-slots 96
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except Exception as exc:  # pragma: no cover
    print(f"ERROR: PyMuPDF/fitz is required to read PDFs: {exc}", file=sys.stderr)
    sys.exit(2)

BAD_TOKENS = [
    "SKILL.md",
    "references/",
    "assets/",
    "/Users/",
    "gaokao-advisor",
    "模板",
    "生成器",
    "待补",
    "待查",
    "[URL]",
    "...",
    "🔴",
    "🟡",
    "🟢",
    "✅",
    "❌",
]

REQUIRED_REPORT_TOKENS = [
    "志愿表填写顺序卡片",
    "学生基本信息",
    "个人画像",
    "冲稳保",
    "推荐院校清单",
    "候选剔除日志",
    "敏感性分析",
    "退档风险自查",
    "征集志愿",
    "数据来源",
    "免责声明",
]


def read_pdf_pages(path: Path) -> list[str]:
    """读取 PDF 每页文本。"""
    doc = fitz.open(str(path))
    return [page.get_text() for page in doc]


def pdf_quality_issues(
    path: Path,
    pages: list[str],
    *,
    label: str,
    min_average_chars: int,
    min_file_size: int,
    min_sample_blocks: int,
    reject_builtin_heiti: bool = True,
) -> list[str]:
    """检查 PDF 是否像真实渲染产物，而不是仅能抽取少量文本的伪报告。"""
    issues: list[str] = []
    page_count = len(pages)
    if page_count == 0:
        return [f"{label} PDF has no pages"]

    file_size = path.stat().st_size
    expected_min_size = max(min_file_size, page_count * 1500)
    if file_size < expected_min_size:
        issues.append(
            f"{label} PDF is suspiciously small: {file_size} bytes for {page_count} pages"
        )

    if page_count >= 3:
        average_chars = sum(len(page.strip()) for page in pages) / page_count
        if average_chars < min_average_chars:
            issues.append(
                f"{label} PDF has too little extracted text per page: "
                f"{average_chars:.1f} < {min_average_chars}"
            )

    sample_indices = sorted({0, min(1, page_count - 1), page_count // 2, page_count - 1})
    block_counts: list[int] = []
    font_names: set[str] = set()
    with fitz.open(str(path)) as doc:
        for index in sample_indices:
            page = doc[index]
            blocks = [
                block for block in page.get_text("blocks")
                if len(block) >= 5 and str(block[4]).strip()
            ]
            block_counts.append(len(blocks))
            for font in page.get_fonts(full=True):
                if len(font) > 3 and font[3]:
                    font_names.add(str(font[3]).split("+")[-1])

    if max(block_counts or [0]) < min_sample_blocks:
        issues.append(
            f"{label} PDF has too few rendered text blocks on sampled pages: "
            f"{block_counts}"
        )
    if reject_builtin_heiti and page_count >= 3 and font_names and font_names <= {"Heiti"}:
        issues.append(
            f"{label} PDF uses only PyMuPDF built-in Heiti font; render with pandoc/xelatex"
        )

    return issues


def find_bad_tokens(text: str) -> list[str]:
    """返回文本中出现的禁止词。"""
    return [token for token in BAD_TOKENS if token in text]


def count_card_slots(markdown_text: str) -> int:
    """统计志愿卡片中出现的不同填报位数量。"""
    slots = {int(m.group(1)) for m in re.finditer(r"位\s*(\d{1,3})(?=\D)", markdown_text)}
    return len(slots)


def repeated_prose_issues(markdown_text: str, *, max_repeats: int = 3) -> list[str]:
    """Reject long prose paragraphs that are repeated enough to look like filler."""
    counts: dict[str, int] = {}
    for raw_unit in re.split(r"\n\s*\n", markdown_text):
        unit = " ".join(line.strip() for line in raw_unit.splitlines() if line.strip())
        unit = re.sub(r"\s+", " ", unit).strip()
        if len(unit) < 45:
            continue
        if unit.startswith(("#", "|", "---", "\\", "- 位 ")):
            continue
        if re.fullmatch(r"[\|\-\s:：]+", unit):
            continue
        counts[unit] = counts.get(unit, 0) + 1

    issues: list[str] = []
    for unit, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        if count > max_repeats:
            issues.append(f"repeated prose appears {count} times: {unit[:90]}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--card", required=True, type=Path)
    parser.add_argument("--source-md", required=True, type=Path)
    parser.add_argument("--emergency", required=True, type=Path)
    parser.add_argument("--student-name", required=True)
    parser.add_argument("--expected-slots", required=True, type=int)
    args = parser.parse_args()

    errors: list[str] = []
    for path in [args.report, args.card, args.source_md, args.emergency]:
        if not path.exists():
            errors.append(f"missing file: {path}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    report_pages = read_pdf_pages(args.report)
    card_pages = read_pdf_pages(args.card)
    emergency_pages = read_pdf_pages(args.emergency)
    source_md = args.source_md.read_text(encoding="utf-8")

    report_text = "\n".join(report_pages)
    card_text = "\n".join(card_pages)
    emergency_text = "\n".join(emergency_pages)
    all_text = "\n".join([report_text, card_text, emergency_text, source_md])

    report_page_count = len(report_pages)
    card_page_count = len(card_pages)
    emergency_page_count = len(emergency_pages)
    slot_count = count_card_slots(source_md)
    bad_tokens = find_bad_tokens(all_text)
    repeated_prose_errors = repeated_prose_issues(source_md)
    missing_report_tokens = [token for token in REQUIRED_REPORT_TOKENS if token not in report_text]
    pdf_quality_errors: list[str] = []
    pdf_quality_errors.extend(
        pdf_quality_issues(
            args.report,
            report_pages,
            label="report",
            min_average_chars=300,
            min_file_size=30_000,
            min_sample_blocks=3,
        )
    )
    pdf_quality_errors.extend(
        pdf_quality_issues(
            args.card,
            card_pages,
            label="card",
            min_average_chars=140,
            min_file_size=15_000,
            min_sample_blocks=1,
        )
    )
    pdf_quality_errors.extend(
        pdf_quality_issues(
            args.emergency,
            emergency_pages,
            label="emergency",
            min_average_chars=40,
            min_file_size=10_000,
            min_sample_blocks=1,
            reject_builtin_heiti=False,
        )
    )

    if report_page_count < 20:
        errors.append(f"report pages must be >= 20, got {report_page_count}")
    if card_page_count < 1:
        errors.append("card PDF must have at least 1 page")
    if emergency_page_count < 1:
        errors.append("emergency PDF must have at least 1 page")
    if args.student_name not in report_pages[0]:
        errors.append("page 1 must contain student name")
    if slot_count < args.expected_slots:
        errors.append(f"card must contain at least {args.expected_slots} unique slots, got {slot_count}")
    if "{{" in source_md or "}}" in source_md:
        errors.append("source markdown still contains template placeholders")
    if missing_report_tokens:
        errors.append(f"report missing required sections: {missing_report_tokens}")
    if bad_tokens:
        errors.append(f"forbidden tokens found: {bad_tokens}")
    if repeated_prose_errors:
        errors.extend(repeated_prose_errors)
    if pdf_quality_errors:
        errors.extend(pdf_quality_errors)

    print("Validation summary")
    print(f"- report_pages: {report_page_count}")
    print(f"- card_pages: {card_page_count}")
    print(f"- emergency_pages: {emergency_page_count}")
    print(f"- card_slots: {slot_count} / {args.expected_slots}")
    print(f"- missing_report_tokens: {missing_report_tokens}")
    print(f"- bad_tokens: {bad_tokens}")
    print(f"- repeated_prose_errors: {repeated_prose_errors}")
    print(f"- pdf_quality_errors: {pdf_quality_errors}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print("PASS: all gaokao-advisor deliverable checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
