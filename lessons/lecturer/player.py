"""讲课流程：按讲稿逐步执行，响应学生的暂停、跳步和换个讲法。"""

from __future__ import annotations

import asyncio
import contextlib
import sys
import urllib.request

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import async_playwright

from controls import Controls, next_index
from llm import ConfigError, Rewriter, load_env, pick_rewriter, require_deepseek, rewrite
from script import Script, Step
from stage import Stage
from tts import LECTURER_VOICE, TUTOR_VOICE, SentenceStream, synthesize

TUTOR_TIMEOUT = 120  # 秒


class Lecture:
    def __init__(self, script: Script, stage: Stage, controls: Controls,
                 rewriters: list[Rewriter] | None = None) -> None:
        self.script, self.stage, self.controls = script, stage, controls
        self.rewriters = rewriters or []  # 换个讲法：按顺序尝试，第一个失败就用下一个
        self.i = 0
        self.speaker = "讲师"
        self.reexplain = False

    # ---------- 状态显示 ----------
    async def show(self, note: str = "") -> None:
        n = len(self.script.steps)
        if self.controls.paused:
            note = note or "已暂停 · 按空格继续"
        text = f"<b>{self.speaker}</b> · 第 {min(self.i + 1, n)}/{n} 步" + (f" · {note}" if note else "")
        with contextlib.suppress(PlaywrightError):
            await self.stage.status(text, self.controls.paused, can_reexplain=bool(self.rewriters))

    async def on_command(self, cmd: str) -> None:
        was = self.controls.paused
        self.controls.command(cmd)
        if self.controls.paused != was:
            await (self.stage.pause_audio() if self.controls.paused else self.stage.resume_audio())
        await self.show()

    # ---------- 讲 ----------
    async def speak(self, text: str, voice: str = LECTURER_VOICE) -> None:
        audio = await synthesize(text, voice)
        await self.controls.wait_unpaused()
        await self.stage.play(audio)

    async def speak_tutor_answer(self, before: int) -> None:
        """助教一边生成，讲师这边一边按句朗读（助教的声音）。"""
        stream, queue = SentenceStream(), asyncio.Queue()

        async def watch() -> None:
            loop = asyncio.get_running_loop()
            deadline = loop.time() + TUTOR_TIMEOUT
            while loop.time() < deadline:
                text, done, err = await self.stage.tutor_answer(before)
                for sent in stream.feed(text):
                    queue.put_nowait(asyncio.create_task(synthesize(sent, TUTOR_VOICE)))
                if done:
                    if err:
                        print(f"[讲师] 助教出错：{err}", file=sys.stderr)
                    for sent in stream.flush():
                        queue.put_nowait(asyncio.create_task(synthesize(sent, TUTOR_VOICE)))
                    break
                await asyncio.sleep(0.3)
            queue.put_nowait(None)

        watcher = asyncio.create_task(watch())
        self.speaker = "助教"
        try:
            while (job := await queue.get()) is not None:
                audio = await job
                await self.controls.wait_unpaused()
                await self.show()
                await self.stage.play(audio)
        finally:
            watcher.cancel()
            self.speaker = "讲师"

    async def explain_again(self, step: Step) -> None:
        await self.show("在想另一种讲法…")
        context = await self.stage.section_text(step.target, step.nth)
        said = step.explain if step.kind == "quiz" else step.say
        for r in self.rewriters:
            try:
                text = await rewrite(r, self.script.title, said, context)
                break
            except Exception as e:  # 换下一个模型
                print(f"[讲师] {r.name} 换讲法失败：{e}", file=sys.stderr)
        else:
            await self.show("换个讲法失败了，接着往下讲")
            return
        await self.show()
        await self.speak(text)

    async def perform(self, step: Step) -> None:
        if not await self.stage.highlight(step.target, step.nth):
            print(f"[讲师] 步骤 {step.id}：页面上找不到 {step.target}，跳过", file=sys.stderr)
            return
        if self.reexplain:
            self.reexplain = False
            await self.explain_again(step)
            return
        if step.kind == "demo":
            for a in step.actions:
                await self.controls.wait_unpaused()
                await self.stage.act(a)
        await self.speak(step.say)
        if step.kind == "proxy":
            await self.speak_tutor_answer(await self.stage.ask_tutor(step.question))
        if step.kind == "quiz":
            self.controls.pause()
            await self.show("请在页面上作答，答完按空格继续")
            await self.controls.wait_unpaused()
            await self.show()
            if not await self.stage.quiz_answered(step.target, step.nth):
                await self.stage.reveal_quiz(step.target, step.nth)
            await self.speak(step.explain)

    # ---------- 主循环 ----------
    async def run(self, start: int) -> None:
        steps = self.script.steps
        self.i = start
        while self.i < len(steps):
            await self.controls.wait_unpaused()
            await self.show()
            work = asyncio.create_task(self.perform(steps[self.i]))
            jump = asyncio.create_task(self.controls.wait_jump())
            done, _ = await asyncio.wait({work, jump}, return_when=asyncio.FIRST_COMPLETED)
            if jump in done:
                work.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await work
                await self.stage.stop_audio()
                cmd = self.controls.take_jump() or "next"
                self.reexplain = cmd == "reexplain" and bool(self.rewriters)
                self.i = next_index(self.i, cmd, len(steps))
            else:
                jump.cancel()
                work.result()  # 让步骤里的异常浮上来
                self.i += 1
                await asyncio.sleep(0.35)  # 步骤之间留一口气
        await self.show("本课讲完了 🎉")


def check_server(base: str) -> None:
    try:
        urllib.request.urlopen(base, timeout=3).close()
    except OSError as e:
        raise SystemExit(f"连不上课程服务 {base}（{e}）。请先在另一个终端运行：just super-agent-course")


def build_rewriters(env: dict[str, str]) -> list[Rewriter]:
    """Kimi 优先；Kimi 出错时退到 DeepSeek。"""
    first = pick_rewriter(env)
    if first.name == "DeepSeek":
        return [first]
    return [first, pick_rewriter({k: v for k, v in env.items() if k != "MOONSHOT_API_KEY"})]


async def run_lecture(script: Script, base: str, start: int = 0, headless: bool = False) -> None:
    env = load_env()
    try:
        require_deepseek(env)
    except ConfigError as e:
        raise SystemExit(str(e))
    check_server(base)
    rewriters = build_rewriters(env)
    print(f"[讲师] 换个讲法使用：{' → '.join(r.name for r in rewriters)}")
    controls = Controls()
    async with async_playwright() as pw:
        holder: dict[str, Lecture] = {}
        stage = await Stage.open(pw, base, script.lesson,
                                 lambda cmd: asyncio.ensure_future(holder["l"].on_command(cmd)), headless)
        lecture = holder["l"] = Lecture(script, stage, controls, rewriters)
        try:
            await lecture.run(start)
            if not headless:
                await stage.wait_closed()
        except PlaywrightError as e:
            if "closed" not in str(e).lower():
                raise
            print("[讲师] 浏览器已关闭，下课。")
        finally:
            with contextlib.suppress(Exception):
                await stage.close()
