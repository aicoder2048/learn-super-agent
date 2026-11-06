"""AI 讲师入口。

    uv run lecturer.py audio SA02            预合成一课讲师音频
    uv run lecturer.py run SA02 [--from s3]  开讲，讲完自动进入下一课（需先启动 just super-agent-course）
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from script import Script, ScriptError, load_script
from tts import LECTURER_VOICE, synthesize

HERE = Path(__file__).parent
DEFAULT_PORT = 8766


def course_url(port: int) -> str:
    if not 1 <= port <= 65535:
        raise SystemExit(f"端口号不合法：{port}")
    return f"http://127.0.0.1:{port}/lessons/"


def script_path(lesson_id: str) -> Path:
    return HERE / "scripts" / f"{lesson_id.upper()}.json"


def lesson_sequence(first: str, scripts_dir: Path = HERE / "scripts") -> list[str]:
    """从 first 开始、按课号排序的所有有讲稿的课。讲完一课自动进入下一课。"""
    first = first.upper()
    ids = sorted(p.stem for p in scripts_dir.glob("SA*.json"))
    if first not in ids:
        raise ScriptError(f"没有 {first} 的讲稿（{scripts_dir}）")
    return ids[ids.index(first):]


async def prepare_audio(script: Script) -> None:
    texts = script.lecturer_texts()
    for i, t in enumerate(texts, 1):
        p = await synthesize(t, LECTURER_VOICE)
        print(f"[{i}/{len(texts)}] {p.name}  {t[:24]}…")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AI 讲师")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("audio", help="预合成一课的讲师音频")
    a.add_argument("lesson")
    r = sub.add_parser("run", help="开讲")
    r.add_argument("lesson")
    r.add_argument("--from", dest="start", default=None, help="从哪个小节开始，如 s3")
    r.add_argument("--port", type=int, default=DEFAULT_PORT,
                   help=f"课程服务端口，要和 just super-agent-course 用的一致（默认 {DEFAULT_PORT}）")
    args = ap.parse_args(argv)

    try:
        if args.cmd == "run":
            from player import run_lecture

            lessons = [(lid, load_script(script_path(lid))) for lid in lesson_sequence(args.lesson)]
            start = lessons[0][1].start_index(args.start) if args.start else 0
            asyncio.run(run_lecture(lessons, course_url(args.port), start))
            return 0
        script = load_script(script_path(args.lesson))
        if args.cmd == "audio":
            asyncio.run(prepare_audio(script))
            return 0
    except ScriptError as e:
        print(f"讲稿错误：{e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:  # Ctrl+C 是正常下课
        print("\n[讲师] 下课。")
        return 0


if __name__ == "__main__":
    sys.exit(main())
