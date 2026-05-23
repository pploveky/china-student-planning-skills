#!/usr/bin/env python3
"""高考志愿批量任务调度脚本。

用途：
- 将批量学生 xlsx 拆成逐学生任务包，并维护任务状态与交付物汇总。

核心逻辑：
1. 调用 parse_students_xlsx.py 解析 29 列学生信息，生成每个学生的 task.json 与 task_prompt.md。
2. 使用 .checkpoint.json 记录 pending、running、done、failed 状态，支持断点续跑。
3. 生成 _errors.csv 与 _summary.csv，便于批量交付时排查失败行和汇总产物路径。
4. 本脚本只负责调度和状态管理，不内联执行联网检索、论证和 PDF 生成主流程。

输入输出：
- 输入：批量学生 xlsx、输出目录，以及 mark-done/mark-failed 的状态参数。
- 输出：逐学生任务目录、checkpoint、错误清单和汇总 CSV。

关键依赖：
- Python 3.10+
- parse_students_xlsx.py

最小使用示例：
    python3 batch_generate.py prepare input/students.xlsx output/
    python3 batch_generate.py list output/
    python3 batch_generate.py summary output/
"""
from __future__ import annotations
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parse_students_xlsx import parse_xlsx  # noqa: E402


def _student_dir(out_root: Path, name: str) -> Path:
    """规范化学生目录名（避免路径非法字符）。"""
    safe = name.replace("/", "_").replace("\\", "_").strip()
    return out_root / safe


def _load_checkpoint(out_root: Path) -> dict:
    cp = out_root / ".checkpoint.json"
    if cp.exists():
        return json.loads(cp.read_text(encoding="utf-8"))
    return {"students": {}}


def _save_checkpoint(out_root: Path, data: dict) -> None:
    (out_root / ".checkpoint.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _gen_task_prompt(student: dict) -> str:
    """为单个学生生成一段可直接喂给 主流程执行者的任务 prompt。"""
    s = student
    code = s.get("学生代号") or s["学生姓名"]
    return f"""# 单学生志愿建议任务（批量模式 · 自动生成 prompt）

> 本任务来自批量 xlsx，跳过阶段 1 反问，直接进入阶段 2-7。
> 全文使用代号 **{code}** 替代真名（除非代号留空）。

## 学生信息（已通过 29 列校验）

| 字段 | 值 |
|------|---|
| 主要决策者 | {s['主要决策者']} |
| 省份 / 户籍 | {s['省份']} / {s['户籍']} |
| 高考年份 | {s['高考年份']} |
| 科类_选科 | {s['科类_选科']} |
| 总分 / 位次 | {s['总分']} / {s['全省位次']}{' (待反推)' if s['全省位次'] == 0 else ''} |
| 语数外 | {s['语文分']} / {s['数学分']} / {s['外语分']}（{s.get('外语语种') or '英语'}）|
| 兴趣方向 | {s['兴趣方向']} |
| 厌恶清单 | {s.get('厌恶清单') or '无'} |
| 梦想校 | {s.get('梦想校') or '未指定'} |
| 性格倾向 | {s['性格倾向']} |
| 地域偏好 / 排斥 | {s['地域偏好']} / {s.get('排斥地域') or '无'} |
| 优先级 | {s['优先级排序']} |
| 学费上限 | {s['学费上限_万每年']} 万/年 |
| 接受民办 / 中外合办 | {'是' if s['接受民办_独立学院'] else '否'} / {'是' if s['接受中外合办'] else '否'} |
| 服从调剂 / 读研意向 | {'是' if s['服从专业调剂'] else '否'} / {s['读研意向']} |
| 家庭月收入 | {s['家庭月收入_万']} 万 |
| 体检受限项 | {s['体检受限项']} |
| 特殊招生通道 | {s['特殊招生通道']} |
| 备注 | {s.get('备注') or '无'} |

## 执行要求

1. 严格按 SKILL.md 阶段 2-7 执行
2. 检索数据走"7 个手段穷尽核实"，禁止 D/E 级源
3. 输出 4 件交付物到当前目录：
   - `{code}_志愿建议报告_{s['高考年份']}.pdf`
   - `{code}_志愿表填写顺序.pdf`
   - `{code}_志愿建议报告.md`
   - `{code}_应急一页纸.pdf`
4. 完成后调用 batch_generate.py mark-done 标记
"""


def cmd_prepare(xlsx_path: Path, out_root: Path) -> None:
    """解析 xlsx 并为每个学生创建任务目录与 task_prompt.md。"""
    out_root.mkdir(parents=True, exist_ok=True)
    rows, errors = parse_xlsx(xlsx_path)

    # 行错误清单
    err_csv = out_root / "_errors.csv"
    with err_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["row", "name", "errors"])
        for e in errors:
            w.writerow([e["row"], e["name"] or "", "; ".join(e["errors"])])

    # 加载已有 checkpoint，增量更新
    cp = _load_checkpoint(out_root)
    new_count = 0
    for s in rows:
        name = s["学生姓名"]
        if not name:
            continue
        sd = _student_dir(out_root, name)
        sd.mkdir(parents=True, exist_ok=True)
        # 写 task.json
        (sd / "task.json").write_text(
            json.dumps({k: v for k, v in s.items() if k != "_row"},
                       ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        # 写 task_prompt.md
        (sd / "task_prompt.md").write_text(_gen_task_prompt(s), encoding="utf-8")
        # checkpoint 中的状态：保持已存在的，否则 pending
        st = cp["students"].get(name, {}).get("status", "pending")
        cp["students"][name] = {
            "status": st,
            "code": s.get("学生代号") or name,
            "dir": str(sd.relative_to(out_root)),
            "省份": s["省份"],
            "选科": s["科类_选科"],
            "总分": s["总分"],
            "更新时间": datetime.now().isoformat(timespec="seconds"),
        }
        if st == "pending":
            new_count += 1
    _save_checkpoint(out_root, cp)

    print(f"已准备 {len(rows)} 个学生任务（pending {new_count}）→ {out_root}")
    print(f"行错误清单: {err_csv}（{len(errors)} 行错误）")


def cmd_list(out_root: Path, status: str = "pending") -> None:
    cp = _load_checkpoint(out_root)
    rows = [
        (n, info) for n, info in cp["students"].items()
        if status == "all" or info["status"] == status
    ]
    if not rows:
        print(f"无 {status} 状态学生")
        return
    print(f"{'学生':<24} {'状态':<10} {'省份':<8} {'选科':<10} {'总分':<5}")
    for n, info in rows:
        print(f"{n:<24} {info['status']:<10} {info['省份']:<8} "
              f"{info['选科']:<10} {info['总分']}")


def cmd_mark_done(out_root: Path, name: str, files: list[str]) -> None:
    cp = _load_checkpoint(out_root)
    if name not in cp["students"]:
        print(f"未知学生 {name}", file=sys.stderr)
        sys.exit(1)
    cp["students"][name]["status"] = "done"
    cp["students"][name]["files"] = files
    cp["students"][name]["完成时间"] = datetime.now().isoformat(timespec="seconds")
    _save_checkpoint(out_root, cp)
    print(f"[done] {name}（{len(files)} 件交付物）")


def cmd_mark_failed(out_root: Path, name: str, err: str) -> None:
    cp = _load_checkpoint(out_root)
    if name not in cp["students"]:
        print(f"未知学生 {name}", file=sys.stderr)
        sys.exit(1)
    cp["students"][name]["status"] = "failed"
    cp["students"][name]["error"] = err
    cp["students"][name]["失败时间"] = datetime.now().isoformat(timespec="seconds")
    _save_checkpoint(out_root, cp)
    print(f"[failed] {name}: {err}")


def cmd_summary(out_root: Path) -> None:
    cp = _load_checkpoint(out_root)
    out_csv = out_root / "_summary.csv"
    cnt = {"pending": 0, "running": 0, "done": 0, "failed": 0}
    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["学生", "代号", "状态", "省份", "选科", "总分",
                    "交付物数", "错误"])
        for name, info in cp["students"].items():
            cnt[info["status"]] = cnt.get(info["status"], 0) + 1
            w.writerow([
                name, info.get("code", ""), info["status"],
                info["省份"], info["选科"], info["总分"],
                len(info.get("files", [])),
                info.get("error", ""),
            ])
    print(f"汇总写入 {out_csv}")
    print(f"  pending={cnt['pending']}  running={cnt['running']}  "
          f"done={cnt['done']}  failed={cnt['failed']}")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    sub = sys.argv[1]
    if sub == "prepare":
        cmd_prepare(Path(sys.argv[2]), Path(sys.argv[3]))
    elif sub == "list":
        out = Path(sys.argv[2])
        st = sys.argv[3] if len(sys.argv) > 3 else "pending"
        cmd_list(out, st)
    elif sub == "mark-done":
        cmd_mark_done(Path(sys.argv[2]), sys.argv[3], sys.argv[4:])
    elif sub == "mark-failed":
        cmd_mark_failed(Path(sys.argv[2]), sys.argv[3], sys.argv[4])
    elif sub == "summary":
        cmd_summary(Path(sys.argv[2]))
    else:
        print(f"未知子命令 {sub}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
