#!/usr/bin/env bash
# 高考志愿报告 Markdown 转 PDF 脚本。
#
# 用途：
#   将 Markdown 报告转换为 PDF，优先使用 macOS 常见中文字体，兼容 Linux 字体环境。
#
# 核心逻辑：
#   1. 校验输入 Markdown 是否存在。
#   2. 自动判断卡片、一页纸等短文档是否禁用目录。
#   3. 按 pandoc+xelatex、pandoc+wkhtmltopdf、md-to-pdf 的顺序选择可用渲染方案。
#   4. 自动探测中文字体，按可用性选择第一个候选字体。
#
# 输入输出：
#   输入：Markdown 文件路径、PDF 输出路径、可选字体名、可选 --no-toc。
#   输出：PDF 文件；没有可用渲染工具时返回 2。
#
# 关键依赖：
#   pandoc + xelatex（推荐），或 pandoc + wkhtmltopdf，或 md-to-pdf。
#
# 最小使用示例：
#   bash md_to_pdf.sh report.md report.pdf
#
# 字体回退顺序：
#   Songti SC → STSong → STHeiti → Hiragino Sans GB → Noto Sans CJK SC → Arial Unicode MS
#
# --no-toc：不生成目录（卡片类短文档建议加；主报告默认带目录）

set -e

INPUT="$1"
OUTPUT="$2"
FONT_OVERRIDE="$3"
NO_TOC=""
for arg in "$@"; do
  if [[ "$arg" == "--no-toc" ]]; then
    NO_TOC="1"
  fi
done

if [[ -z "$INPUT" || -z "$OUTPUT" ]]; then
  echo "用法: bash md_to_pdf.sh <input.md> <output.pdf> [font_name] [--no-toc]" >&2
  exit 1
fi

if [[ ! -f "$INPUT" ]]; then
  echo "输入文件不存在: $INPUT" >&2
  exit 1
fi

# 自动判定：文件名含"卡片|顺序|应急|一页"时强制 --no-toc
basename_in=$(basename "$INPUT")
if [[ "$basename_in" == *"卡片"* || "$basename_in" == *"顺序"* || "$basename_in" == *"应急"* || "$basename_in" == *"一页"* ]]; then
  NO_TOC="1"
fi

TOC_ARGS="--toc --toc-depth=2"
if [[ "$NO_TOC" == "1" ]]; then
  TOC_ARGS=""
fi

# 探测可用中文字体
detect_font() {
  if [[ -n "$FONT_OVERRIDE" ]]; then
    echo "$FONT_OVERRIDE"
    return
  fi
  # 通过创建一个微型测试文件来探测字体可用性
  local candidates=("Songti SC" "STSong" "STHeiti" "Hiragino Sans GB" "Noto Sans CJK SC" "Arial Unicode MS")
  local tmpdir=$(mktemp -d)
  for f in "${candidates[@]}"; do
    cat > "$tmpdir/probe.tex" <<EOF
\\documentclass{article}
\\usepackage{fontspec}
\\setmainfont{$f}
\\begin{document}测试\\end{document}
EOF
    if (cd "$tmpdir" && xelatex -interaction=nonstopmode probe.tex >/dev/null 2>&1) && [[ -f "$tmpdir/probe.pdf" ]]; then
      rm -rf "$tmpdir"
      echo "$f"
      return
    fi
    rm -f "$tmpdir/probe.pdf"
  done
  rm -rf "$tmpdir"
  echo "Songti SC"  # 兜底
}

# 方案 1：pandoc + xelatex（推荐）
if command -v pandoc >/dev/null 2>&1 && command -v xelatex >/dev/null 2>&1; then
  FONT=$(detect_font)
  echo "使用 pandoc + xelatex 生成 PDF（中文字体: $FONT）..."
  pandoc "$INPUT" \
    -o "$OUTPUT" \
    --pdf-engine=xelatex \
    -V CJKmainfont="$FONT" \
    -V mainfont="$FONT" \
    -V geometry:margin=2.2cm \
    -V linkcolor=blue \
    $TOC_ARGS
  echo "完成: $OUTPUT"
  exit 0
fi

# 方案 2：pandoc + wkhtmltopdf
if command -v pandoc >/dev/null 2>&1 && command -v wkhtmltopdf >/dev/null 2>&1; then
  echo "使用 pandoc + wkhtmltopdf 生成 PDF..."
  pandoc "$INPUT" -o "$OUTPUT" --pdf-engine=wkhtmltopdf \
    -V margin-top=22mm -V margin-left=22mm -V margin-right=22mm -V margin-bottom=22mm \
    $TOC_ARGS
  echo "完成: $OUTPUT"
  exit 0
fi

# 方案 3：md-to-pdf (npm)
if command -v md-to-pdf >/dev/null 2>&1; then
  echo "使用 md-to-pdf 生成 PDF..."
  md-to-pdf "$INPUT" --dest "$(dirname "$OUTPUT")"
  GEN_FILE="$(dirname "$OUTPUT")/$(basename "$INPUT" .md).pdf"
  if [[ -f "$GEN_FILE" && "$GEN_FILE" != "$OUTPUT" ]]; then
    mv "$GEN_FILE" "$OUTPUT"
  fi
  echo "完成: $OUTPUT"
  exit 0
fi

echo "错误：未找到可用的 PDF 转换工具。请先安装其中之一：" >&2
echo "  - pandoc + MacTeX/BasicTeX（推荐）" >&2
echo "  - pandoc + wkhtmltopdf" >&2
echo "  - npm install -g md-to-pdf" >&2
exit 2
