"""AI 讲师入口。

    uv run lecturer.py audio SA02            预合成一课讲师音频
    uv run lecturer.py run SA02 [--from s3]  开讲（需先启动 just super-agent-course）
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
        script = load_script(script_path(args.lesson))
        if args.cmd == "audio":
            asyncio.run(prepare_audio(script))
            return 0
        from player import run_lecture

        start = script.start_index(args.start) if args.start else 0
        asyncio.run(run_lecture(script, course_url(args.port), start))
        return 0
    except ScriptError as e:
        print(f"讲稿错误：{e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:  # Ctrl+C 是正常下课
        print("\n[讲师] 下课。")
        return 0


if __name__ == "__main__":
    sys.exit(main())
