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
        self.known_answers = 0       # 已经处理过的助教回答条数
        self.proxy_active = False    # 讲师正在代问，新回答不算学生的
        self.reading: asyncio.Task | None = None  # 正在朗读学生提问的回答

    # ---------- 状态显示 ----------
    async def show(self, note: str = "") -> None:
        n = len(self.script.steps)
        if self.controls.paused:
            note = note or "已暂停 · 按空格继续"
        text = f"<b>{self.speaker}</b> · 第 {min(self.i + 1, n)}/{n} 步" + (f" · {note}" if note else "")
        with contextlib.suppress(PlaywrightError):
            await self.stage.status(text, self.controls.paused, can_reexplain=bool(self.rewriters))

    async def on_command(self, cmd: str) -> None:
        if self.reading and not self.reading.done():
            await self.stop_reading()
            if cmd == "toggle":  # 空格只打断朗读，讲课仍保持暂停
                await self.show()
                return
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

    async def speak_tutor_answer(self, before: int, aside: bool = False) -> None:
        """助教一边生成，这边一边按句朗读（助教的声音）。

        aside=True 用于学生自己的提问：走第二路音频，暂停时也照常读。
        """
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
                if aside:
                    await self.show("在回答你的问题 · 空格停止朗读")
                    await self.stage.play_aside(audio)
                else:
                    await self.controls.wait_unpaused()
                    await self.show()
                    await self.stage.play(audio)
        finally:
            watcher.cancel()
            self.speaker = "讲师"
            if aside:
                await self.show()

    # ---------- 学生自己问助教 ----------
    async def stop_reading(self) -> None:
        if self.reading:
            self.reading.cancel()
            with contextlib.suppress(asyncio.CancelledError, PlaywrightError):
                await self.reading
            self.reading = None
        with contextlib.suppress(PlaywrightError):
            await self.stage.stop_aside()

    async def watch_student_questions(self) -> None:
        """发现学生在右栏新问的问题，就朗读助教的回答；讲师正在讲时先暂停讲课。"""
        self.known_answers = await self.stage.tutor_answer_count()
        while True:
            await asyncio.sleep(0.5)
            count = await self.stage.tutor_answer_count()
            if self.proxy_active or count <= self.known_answers:
                if not self.proxy_active:
                    self.known_answers = min(self.known_answers, count)  # 学生清空过对话
                continue
            index, self.known_answers = self.known_answers, count
            await self.stop_reading()
            if not self.controls.paused:
                self.controls.pause()
                await self.stage.pause_audio()
            self.reading = asyncio.create_task(self.speak_tutor_answer(index, aside=True))

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
            self.proxy_active = True
            try:
                before = await self.stage.ask_tutor(step.question)
                self.known_answers = before + 1
            finally:
                self.proxy_active = False
            await self.speak_tutor_answer(before)
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
            try:
                done, _ = await asyncio.wait({work, jump}, return_when=asyncio.FIRST_COMPLETED)
            except asyncio.CancelledError:  # Ctrl+C：连同子任务一起收拾干净
                await cancel_all(work, jump)
                raise
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

    async def handoff(self, next_id: str, seconds: int = 5) -> None:
        """讲完一课后倒数几秒进入下一课。学生按空格（或在问助教）就留在本课，再按空格才继续。"""
        self.controls.take_jump()
        for left in range(seconds, 0, -1):
            if self.controls.paused:
                break
            await self.show(f"本课讲完了 · {left} 秒后进入 {next_id}，按空格留在本课")
            await asyncio.sleep(1)
        if self.controls.paused:
            await self.show(f"留在本课 · 按空格进入 {next_id}")
            await self.controls.wait_unpaused()
        self.controls.take_jump()


async def cancel_all(*tasks: asyncio.Task | None) -> None:
    """取消并等待子任务结束，吞掉它们的异常（浏览器可能已经关了）。"""
    live = [t for t in tasks if t and not t.done()]
    for t in live:
        t.cancel()
    await asyncio.gather(*[t for t in tasks if t], return_exceptions=True)


def check_server(base: str) -> None:
    try:
        urllib.request.urlopen(base, timeout=3).close()
    except OSError as e:
        raise SystemExit(f"连不上课程服务 {base}（{e}）。请先启动课程服务（tools/serve.py），"
                         "或者用 tools/course.py --lecture 一条命令同时启动；端口不一样时给讲师加上同样的 --port。")


def build_rewriters(env: dict[str, str]) -> list[Rewriter]:
    """Kimi 优先；Kimi 出错时退到 DeepSeek。"""
    first = pick_rewriter(env)
    if first.name == "DeepSeek":
        return [first]
    return [first, pick_rewriter({k: v for k, v in env.items() if k != "MOONSHOT_API_KEY"})]


async def run_lecture(lessons: list[tuple[str, Script]], base: str, start: int = 0,
                      headless: bool = False) -> None:
    """按顺序讲 lessons（课号, 讲稿）；讲完一课自动进入下一课。start 只作用于第一课。"""
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
        stage = await Stage.open(pw, base, lessons[0][1].lesson,
                                 lambda cmd: asyncio.ensure_future(holder["l"].on_command(cmd)), headless)
        lecture: Lecture | None = None
        student: asyncio.Task | None = None
        try:
            for k, (lesson_id, script) in enumerate(lessons):
                if k:
                    await stage.goto(script.lesson)
                print(f"[讲师] 开讲 {lesson_id} {script.title}")
                lecture = holder["l"] = Lecture(script, stage, controls, rewriters)
                student = asyncio.create_task(lecture.watch_student_questions())
                await lecture.run(start if k == 0 else 0)
                if k + 1 < len(lessons):
                    await lecture.handoff(lessons[k + 1][0])
                    await cancel_all(student, lecture.reading)
            if not headless:
                await stage.wait_closed()  # 全部讲完后，学生的提问照样朗读
        except PlaywrightError as e:
            if "closed" not in str(e).lower():
                raise
            print("[讲师] 浏览器已关闭，下课。")
        finally:
            await cancel_all(student, lecture.reading if lecture else None)
            with contextlib.suppress(Exception):
                await stage.close()
