"""端到端冒烟：真浏览器（无界面）+ 真课程服务 + 真 TTS。服务没起时跳过。"""

import asyncio
import json
import urllib.request

import pytest

BASE = "http://127.0.0.1:8766/lessons/"


def server_up() -> bool:
    try:
        urllib.request.urlopen(BASE, timeout=2).close()
        return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(not server_up(), reason="课程服务未启动（just super-agent-course）")

SMOKE = {
    "lesson": "SA02-two-layer.html",
    "title": "冒烟",
    "steps": [
        {"id": "s1-01", "section": "s1", "kind": "say", "target": "#s1 h2", "say": "第一步。"},
        {"id": "s1-02", "section": "s1", "kind": "demo", "target": "#demo1",
         "actions": [{"set": "#d1-g", "value": "0.5"}], "say": "调好了。"},
        {"id": "s6-01", "section": "s6", "kind": "quiz", "target": "#s6 .quiz", "nth": 1,
         "say": "做题。", "explain": "答案是 C。"},
    ],
}


def test_smoke_lecture(tmp_path):
    from playwright.async_api import async_playwright

    from controls import Controls
    from player import Lecture
    from script import load_script
    from stage import Stage

    p = tmp_path / "SMOKE.json"
    p.write_text(json.dumps(SMOKE, ensure_ascii=False), encoding="utf-8")
    script = load_script(p)

    async def go():
        controls = Controls()
        async with async_playwright() as pw:
            holder = {}
            stage = await Stage.open(pw, BASE, script.lesson,
                                     lambda c: asyncio.ensure_future(holder["l"].on_command(c)), headless=True)
            lec = holder["l"] = Lecture(script, stage, controls)
            run = asyncio.create_task(lec.run(0))
            # 等到自测题自动暂停，模拟学生没作答直接按空格
            for _ in range(200):
                if controls.paused:
                    break
                await asyncio.sleep(0.1)
            assert controls.paused and lec.i == 2
            assert await stage.page.input_value("#d1-g") == "0.5"
            await stage.page.keyboard.press("Space")
            await asyncio.wait_for(run, 30)
            assert await stage.quiz_answered("#s6 .quiz", 1)  # 讲师替学生点出了答案
            bar = await stage.page.inner_text(".lecturer-bar .who")
            assert "讲完" in bar
            await stage.close()

    asyncio.run(go())


def test_next_key_skips_current_step(tmp_path):
    from playwright.async_api import async_playwright

    from controls import Controls
    from player import Lecture
    from script import load_script
    from stage import Stage

    data = dict(SMOKE, steps=SMOKE["steps"][:2])
    data["steps"] = [dict(data["steps"][0], say="这是一段比较长的讲解，用来测试按右方向键能不能立刻跳到下一步。")] + data["steps"][1:]
    p = tmp_path / "SMOKE.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    script = load_script(p)

    async def go():
        controls = Controls()
        async with async_playwright() as pw:
            holder = {}
            stage = await Stage.open(pw, BASE, script.lesson,
                                     lambda c: asyncio.ensure_future(holder["l"].on_command(c)), headless=True)
            lec = holder["l"] = Lecture(script, stage, controls)
            run = asyncio.create_task(lec.run(0))
            await asyncio.sleep(4)  # 第一段正在播
            assert lec.i == 0
            await stage.page.keyboard.press("ArrowRight")
            await asyncio.sleep(0.5)
            assert lec.i == 1
            await asyncio.wait_for(run, 30)
            await stage.close()

    asyncio.run(go())
