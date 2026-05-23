#!/usr/bin/env python3
"""就业建议报告交付物校验脚本。

用途：
- 检查主报告 PDF 页数、封面/目录/摘要顺序
- 检查 35 周求职日历 PDF 页数与 Week 1-35 完整展开
- 检查目标公司清单 CSV 行数
- 检测内部路径、占位符、压缩日历等不应出现在交付物中的内容

核心逻辑：
1. 使用 PyMuPDF 读取 PDF 文本与页数。
2. 使用 csv 模块统计目标公司清单行数。
3. 用固定黑名单扫描内部痕迹和占位符。
4. 任一硬性门禁失败即返回非零退出码。

输入输出：
- 输入：主报告 PDF、日历 PDF、公司清单 CSV、学生姓名。
- 输出：终端校验摘要；成功返回 0，失败返回 1，依赖缺失返回 2。

关键依赖：
- Python 3.10+
- PyMuPDF（fitz）

最小使用示例：
    python3 validate_outputs.py --report report.pdf --calendar calendar.pdf --csv companies.csv --student-name 张同学
"""

from __future__ import annotations

import argparse
import csv
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
    "career-advisor",
    "模板",
    "生成器",
    "详见",
    "待补",
    "待查",
    "Week 8 - Week 14",
    "此 7 周关键节奏",
    "同上模板",
    "其他 5 题略",
    "13800138000",
    "zhang@gmail.com",
    "[URL]",
    "...",
]


def read_pdf_pages(path: Path) -> list[str]:
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


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return 0
    return max(0, len(rows) - 1)


def find_bad_tokens(text: str) -> list[str]:
    return [token for token in BAD_TOKENS if token in text]


def calendar_week_numbers(text: str) -> set[int]:
    # Accept Week 1：, Week 1:, Week 1 -, and plain "Week 1" headings.
    nums = set()
    for m in re.finditer(r"Week\s+(\d{1,2})(?=\D)", text):
        n = int(m.group(1))
        if 1 <= n <= 35:
            nums.add(n)
    return nums


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--calendar", required=True, type=Path)
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--student-name", required=True)
    args = parser.parse_args()

    errors: list[str] = []

    for p in [args.report, args.calendar, args.csv]:
        if not p.exists():
            errors.append(f"missing file: {p}")

    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return 1

    report_pages = read_pdf_pages(args.report)
    calendar_pages = read_pdf_pages(args.calendar)
    report_text = "\n".join(report_pages)
    calendar_text = "\n".join(calendar_pages)
    csv_text = args.csv.read_text(encoding="utf-8-sig")
    all_text = report_text + "\n" + calendar_text + "\n" + csv_text

    report_page_count = len(report_pages)
    calendar_page_count = len(calendar_pages)
    csv_rows = count_csv_rows(args.csv)
    weeks = calendar_week_numbers(calendar_text)
    bad_tokens = find_bad_tokens(all_text)
    pdf_quality_errors: list[str] = []
    pdf_quality_errors.extend(
        pdf_quality_issues(
            args.report,
            report_pages,
            label="report",
            min_average_chars=280,
            min_file_size=45_000,
            min_sample_blocks=3,
        )
    )
    pdf_quality_errors.extend(
        pdf_quality_issues(
            args.calendar,
            calendar_pages,
            label="calendar",
            min_average_chars=160,
            min_file_size=25_000,
            min_sample_blocks=2,
        )
    )

    if not (30 <= report_page_count <= 45):
        errors.append(f"report pages must be 30-45, got {report_page_count}")
    if calendar_page_count < 10:
        errors.append(f"calendar pages must be >= 10, got {calendar_page_count}")
    if not (20 <= csv_rows <= 30):
        errors.append(f"csv rows must be 20-30, got {csv_rows}")

    first_page = report_pages[0] if report_pages else ""
    second_page = report_pages[1] if len(report_pages) > 1 else ""
    third_page = report_pages[2] if len(report_pages) > 2 else ""

    if args.student_name not in first_page or "Contents" in first_page or "目录" in first_page:
        errors.append("page 1 must be cover, not table of contents")
    if "Contents" not in second_page and "目录" not in second_page:
        errors.append("page 2 must be table of contents")
    if "摘要" not in third_page:
        errors.append("page 3 must be summary/摘要")

    missing_weeks = sorted(set(range(1, 36)) - weeks)
    if missing_weeks:
        errors.append(f"calendar missing week numbers: {missing_weeks}")

    if bad_tokens:
        errors.append(f"forbidden tokens found: {bad_tokens}")
    if pdf_quality_errors:
        errors.extend(pdf_quality_errors)

    print("Validation summary")
    print(f"- report_pages: {report_page_count}")
    print(f"- calendar_pages: {calendar_page_count}")
    print(f"- csv_rows: {csv_rows}")
    print(f"- calendar_weeks: {len(weeks)} / 35")
    print(f"- bad_tokens: {bad_tokens}")
    print(f"- pdf_quality_errors: {pdf_quality_errors}")

    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return 1

    print("PASS: all career-advisor deliverable checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
