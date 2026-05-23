#!/usr/bin/env python3
"""考研规划交付物校验脚本。

用途：
- 检查考研初试规划主报告和 33–35 周日历附件是否满足发布级硬门禁。

核心逻辑：
1. 使用 PyMuPDF 读取主报告 PDF 与日历 PDF 的文本和页数。
2. 检查主报告页数、封面/摘要、8 章 + 5 附录、决策结论、5 个诊断数字和导师附录结构。
3. 检查日历附件 Week 1 到 Week N 是否完整展开，且不使用压缩表达。
4. 扫描内部路径、占位符、开发词和不适合学生交付的内容。

输入输出：
- 输入：主报告 PDF、日历 PDF、学生姓名、预期周数。
- 输出：终端校验摘要；成功返回 0，失败返回 1，依赖缺失返回 2。

关键依赖：
- Python 3.10+
- PyMuPDF（fitz）

最小使用示例：
    python3 validate_outputs.py --report report.pdf --calendar calendar.pdf --student-name 张同学 --expected-weeks 33
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
    "references/",
    "assets/",
    ".md",
    "/Users/",
    "kaoyan-advisor",
    "模板",
    "生成器",
    "待补",
    "待查",
    "暂无",
    "互证整理",
    "学长贴整理",
    "推荐 1",
    "推荐 2",
    "[URL]",
    "...",
    "🔴",
    "🟡",
    "🟢",
    "✅",
    "❌",
]

COMPRESSED_CALENDAR_TOKENS = [
    "Week 5-Week",
    "Week 5 - Week",
    "第 5 周以后",
    "同上",
    "略",
    "按上述节奏继续",
]

REQUIRED_REPORT_TOKENS = [
    "摘要",
    "个人画像",
    "个性化诊断",
    "当前词汇量",
    "专业课起点分",
    "每周有效小时数",
    "合理目标分区间",
    "合理冲档幅度",
    "候选院校决策矩阵",
    "决策结论",
    "建议",
    "不建议",
    "目标分数",
    "资料与课程清单",
    "公开信息核验",
    "风险与红线",
    "附录 A",
    "附录 B",
    "附录 C",
    "附录 D",
    "D.1",
    "D.2",
    "D.3",
    "附录 E",
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
    if page_count >= 3 and font_names and font_names <= {"Heiti"}:
        issues.append(
            f"{label} PDF uses only PyMuPDF built-in Heiti font; render with pandoc/xelatex"
        )

    return issues


def find_bad_tokens(text: str) -> list[str]:
    """返回文本中出现的禁止词。"""
    return [token for token in BAD_TOKENS if token in text]


def calendar_week_numbers(text: str) -> set[int]:
    """提取日历中的 Week 编号。"""
    weeks: set[int] = set()
    for match in re.finditer(r"Week\s+(\d{1,2})(?=\D)", text):
        week = int(match.group(1))
        if 1 <= week <= 35:
            weeks.add(week)
    return weeks


def contains_required_token(text: str, token: str) -> bool:
    """判断 PDF 文本是否包含必需内容，兼容 XeLaTeX 抽取时去掉中英空格的情况。"""
    if token in text:
        return True
    return re.sub(r"\s+", "", token) in re.sub(r"\s+", "", text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--calendar", required=True, type=Path)
    parser.add_argument("--student-name", required=True)
    parser.add_argument("--expected-weeks", required=True, type=int)
    args = parser.parse_args()

    errors: list[str] = []
    for path in [args.report, args.calendar]:
        if not path.exists():
            errors.append(f"missing file: {path}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    report_pages = read_pdf_pages(args.report)
    calendar_pages = read_pdf_pages(args.calendar)
    report_text = "\n".join(report_pages)
    calendar_text = "\n".join(calendar_pages)
    all_text = report_text + "\n" + calendar_text

    report_page_count = len(report_pages)
    calendar_page_count = len(calendar_pages)
    weeks = calendar_week_numbers(calendar_text)
    missing_weeks = sorted(set(range(1, args.expected_weeks + 1)) - weeks)
    missing_report_tokens = [token for token in REQUIRED_REPORT_TOKENS if not contains_required_token(report_text, token)]
    bad_tokens = find_bad_tokens(all_text)
    compressed_tokens = [token for token in COMPRESSED_CALENDAR_TOKENS if token in calendar_text]
    pdf_quality_errors: list[str] = []
    pdf_quality_errors.extend(
        pdf_quality_issues(
            args.report,
            report_pages,
            label="report",
            min_average_chars=320,
            min_file_size=40_000,
            min_sample_blocks=3,
        )
    )
    pdf_quality_errors.extend(
        pdf_quality_issues(
            args.calendar,
            calendar_pages,
            label="calendar",
            min_average_chars=180,
            min_file_size=20_000,
            min_sample_blocks=2,
        )
    )

    if not (25 <= report_page_count <= 40):
        errors.append(f"report pages must be 25-40, got {report_page_count}")
    if calendar_page_count < 8:
        errors.append(f"calendar pages must be >= 8, got {calendar_page_count}")
    if args.student_name not in report_pages[0]:
        errors.append("page 1 must contain student name")
    if "摘要" not in report_text[:4000]:
        errors.append("summary must appear near the beginning of the report")
    if missing_weeks:
        errors.append(f"calendar missing week numbers: {missing_weeks}")
    if missing_report_tokens:
        errors.append(f"report missing required content: {missing_report_tokens}")
    if bad_tokens:
        errors.append(f"forbidden tokens found: {bad_tokens}")
    if compressed_tokens:
        errors.append(f"compressed calendar tokens found: {compressed_tokens}")
    if pdf_quality_errors:
        errors.extend(pdf_quality_errors)

    print("Validation summary")
    print(f"- report_pages: {report_page_count}")
    print(f"- calendar_pages: {calendar_page_count}")
    print(f"- calendar_weeks: {len(weeks)} / {args.expected_weeks}")
    print(f"- missing_report_tokens: {missing_report_tokens}")
    print(f"- bad_tokens: {bad_tokens}")
    print(f"- compressed_tokens: {compressed_tokens}")
    print(f"- pdf_quality_errors: {pdf_quality_errors}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print("PASS: all kaoyan-advisor deliverable checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
