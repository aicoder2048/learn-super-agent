"""讲台：用 Playwright 操作课程页面（高亮、演示、自测、播放音频）。"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from playwright.async_api import Browser, Page, Playwright

OVERLAY = Path(__file__).with_name("overlay.js")
LAUNCH_ARGS = ["--autoplay-policy=no-user-gesture-required", "--window-size=1500,960"]


async def _launch(pw: Playwright, headless: bool) -> Browser:
    try:  # 优先用本机 Chrome，免下载
        return await pw.chromium.launch(channel="chrome", headless=headless, args=LAUNCH_ARGS)
    except Exception:
        return await pw.chromium.launch(headless=headless, args=LAUNCH_ARGS)


class Stage:
    def __init__(self, browser: Browser, page: Page, base: str) -> None:
        self.browser, self.page, self.base = browser, page, base

    @classmethod
    async def open(cls, pw: Playwright, base: str, lesson: str,
                   on_cmd: Callable[[str], None], headless: bool = False) -> "Stage":
        browser = await _launch(pw, headless)
        ctx = await browser.new_context(no_viewport=True)
        await ctx.add_init_script(path=str(OVERLAY))
        await ctx.expose_binding("__lecturerCmd", lambda _src, cmd: on_cmd(cmd))
        page = await ctx.new_page()
        await page.goto(base + lesson, wait_until="networkidle")
        return cls(browser, page, base)

    async def close(self) -> None:
        await self.browser.close()

    async def wait_closed(self) -> None:
        await self.page.wait_for_event("close", timeout=0)

    # ---------- 讲台反馈 ----------
    async def highlight(self, target: str, nth: int = 0) -> bool:
        return await self.page.evaluate("([s, n]) => __lecturer.highlight(s, n)", [target, nth])

    async def status(self, html: str, paused: bool, can_reexplain: bool) -> None:
        await self.page.evaluate("([h, p, r]) => __lecturer.status(h, p, r)", [html, paused, can_reexplain])

    # ---------- 音频 ----------
    async def play(self, audio: Path) -> None:
        """播放讲稿音频（经课程服务器的 /lessons/lecturer/audio/ 提供），播完才返回。"""
        await self.page.evaluate("u => __lecturer.play(u)", f"{self.base}lecturer/audio/{audio.name}")

    async def pause_audio(self) -> None:
        await self.page.evaluate("__lecturer.pause()")

    async def resume_audio(self) -> None:
        await self.page.evaluate("__lecturer.resume()")

    async def stop_audio(self) -> None:
        await self.page.evaluate("__lecturer.stop()")

    # ---------- 演示 ----------
    async def act(self, action: dict) -> None:
        if "set" in action:
            await self.page.eval_on_selector(
                action["set"],
                "(el, v) => { el.value = v; el.dispatchEvent(new Event('input', {bubbles: true}));"
                " el.dispatchEvent(new Event('change', {bubbles: true})); }",
                str(action["value"]),
            )
        elif "click" in action:
            await self.page.click(action["click"])
        elif "wait" in action:
            await self.page.wait_for_timeout(int(action["wait"]))

    # ---------- 自测 ----------
    async def quiz_answered(self, target: str, nth: int) -> bool:
        return await self.page.evaluate(
            "([s, n]) => !!document.querySelectorAll(s)[n]?.classList.contains('done')", [target, nth])

    async def reveal_quiz(self, target: str, nth: int) -> None:
        """学生没作答时，讲师替他点出正确答案。"""
        await self.page.evaluate(
            "([s, n]) => { const q = document.querySelectorAll(s)[n];"
            " q.querySelectorAll('.opts button')[+q.dataset.answer].click(); }", [target, nth])
