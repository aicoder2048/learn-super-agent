"""端到端冒烟：真浏览器（无界面）+ 真课程服务 + 真 TTS。服务没起时跳过。"""

import asyncio
import json
import urllib.request

import pytest

BASE = "http://127.0.0.1:" + __import__("os").environ.get("LECTURER_TEST_PORT", "8766") + "/lessons/"


def server_up() -> bool:
    try:
        urllib.request.urlopen(BASE, timeout=2).close()
        return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(not server_up(), reason="课程服务未启动（just course）")

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


live_llm = pytest.mark.skipif(
    __import__("os").environ.get("LECTURER_LIVE_LLM") != "1",
    reason="会真实调用 DeepSeek / Kimi，设 LECTURER_LIVE_LLM=1 才跑")


async def _open(script, rewriters=None):
    from playwright.async_api import async_playwright

    from controls import Controls
    from player import Lecture
    from stage import Stage

    pw = await async_playwright().start()
    controls, holder = Controls(), {}
    stage = await Stage.open(pw, BASE, script.lesson,
                             lambda c: asyncio.ensure_future(holder["l"].on_command(c)), headless=True)
    holder["l"] = Lecture(script, stage, controls, rewriters)
    return pw, stage, holder["l"]


def _script(tmp_path, steps):
    from script import load_script

    p = tmp_path / "SMOKE.json"
    p.write_text(json.dumps(dict(SMOKE, steps=steps), ensure_ascii=False), encoding="utf-8")
    return load_script(p)


@live_llm
def test_proxy_question_is_asked_and_answer_spoken(tmp_path):
    step = {"id": "s4-01", "section": "s4", "kind": "proxy", "target": "#s4",
            "say": "我们请助教说说。", "question": "用一句话说：批处理为什么能让 Router 不成为瓶颈？30 字以内。"}
    script = _script(tmp_path, [step])
    spoken = []

    async def go():
        pw, stage, lec = await _open(script)
        orig = stage.play
        stage.play = lambda a: (spoken.append(a), orig(a))[1]
        await asyncio.wait_for(lec.run(0), 120)
        msgs = await stage.page.locator(".tutor-panel .tp-msg").all_inner_texts()
        await stage.close()
        await pw.stop()
        return msgs

    msgs = asyncio.run(go())
    assert any("批处理" in m for m in msgs)  # 问题公开出现在右栏
    assert len(spoken) >= 2  # 讲师引出 + 至少一句助教回答


@live_llm
def test_reexplain_speaks_rewritten_text(tmp_path):
    from llm import load_env
    from player import build_rewriters

    script = _script(tmp_path, [{"id": "s4-01", "section": "s4", "kind": "say", "target": "#s4 h2",
                                 "say": "积压的 Trigger 会合并进下一次 LLM 调用，所以单个 Router 不是瓶颈。"}])
    spoken = []

    async def go():
        pw, stage, lec = await _open(script, build_rewriters(load_env()))
        orig = stage.play
        stage.play = lambda a: (spoken.append(a), orig(a))[1]
        run = asyncio.create_task(lec.run(0))
        await asyncio.sleep(2)
        await stage.page.keyboard.press("r")
        await asyncio.wait_for(run, 120)
        await stage.close()
        await pw.stop()

    asyncio.run(go())
    assert len({a.name for a in spoken}) >= 2  # 原讲解 + 换个讲法的新音频


@live_llm
def test_student_question_answer_is_read_aloud(tmp_path):
    long_say = "这是一段很长的讲解。" * 8
    script = _script(tmp_path, [{"id": "s1-01", "section": "s1", "kind": "say", "target": "#s1 h2", "say": long_say}])
    aside = []

    async def go():
        pw, stage, lec = await _open(script)
        orig = stage.play_aside

        async def spy(a):
            aside.append(a)
            await orig(a)
        stage.play_aside = spy
        watcher = asyncio.create_task(lec.watch_student_questions())
        run = asyncio.create_task(lec.run(0))
        await asyncio.sleep(3)  # 讲师正在讲
        box = stage.page.locator(".tutor-panel textarea")
        await box.fill("用一句话解释 Router，50 字以内。")
        await box.press("Enter")
        await box.evaluate("el => el.blur()")
        for _ in range(300):  # 等助教回答开始被朗读
            if aside:
                break
            await asyncio.sleep(0.1)
        assert aside, "学生提问的回答没有被朗读"
        assert lec.controls.paused and lec.i == 0  # 讲课自动暂停，还停在原步骤
        await stage.page.keyboard.press("Space")  # 暂停朗读
        await asyncio.sleep(0.5)
        assert lec.is_reading and not lec.reading_on.is_set()
        await stage.page.keyboard.press("Space")  # 接着朗读
        await asyncio.sleep(0.5)
        assert lec.reading_on.is_set()
        await stage.page.keyboard.press("Escape")  # 停止朗读
        await asyncio.sleep(0.5)
        assert lec.reading is None and lec.controls.paused
        await stage.page.keyboard.press("Space")  # 继续讲课
        await asyncio.wait_for(run, 60)
        watcher.cancel()
        await stage.close()
        await pw.stop()

    asyncio.run(go())


def test_moves_on_to_next_lesson(tmp_path, monkeypatch):
    import player
    from script import load_script
    from stage import Stage

    def tiny(name, lesson, sec):
        p = tmp_path / f"{name}.json"
        p.write_text(json.dumps({"lesson": lesson, "title": name, "steps": [
            {"id": f"{sec}-01", "section": sec, "kind": "say", "target": f"#{sec} h2", "say": "这一课讲完了。"}]},
            ensure_ascii=False), encoding="utf-8")
        return load_script(p)

    visited = []
    orig = Stage.goto

    async def spy(self, lesson):
        visited.append(lesson)
        await orig(self, lesson)
    monkeypatch.setattr(Stage, "goto", spy)
    lessons = [("SA02", tiny("A", "SA02-two-layer.html", "s1")), ("SA03", tiny("B", "SA03-event-filter-route.html", "s1"))]
    asyncio.run(asyncio.wait_for(player.run_lecture(lessons, BASE, headless=True), 60))
    assert visited == ["SA02-two-layer.html", "SA03-event-filter-route.html"]  # 打开第一课也走 goto


def test_pause_right_after_play_does_not_count_as_finished():
    """play() 刚开始加载就 pause()，浏览器以 AbortError 拒绝 play()：不能当成这段播完了（讲师会跳过这句）。"""
    from playwright.async_api import async_playwright

    from stage import Stage
    from tts import LECTURER_VOICE, synthesize

    async def go():
        async with async_playwright() as pw:
            stage = await Stage.open(pw, BASE, "SA02-two-layer.html", lambda c: None, headless=True)
            url = f"{stage.base}lecturer/audio/{(await synthesize('暂停测试。', LECTURER_VOICE)).name}"
            out = {}
            for fn, pause, resume in (("play", "pause", "resume"), ("playAside", "pauseAside", "resumeAside")):
                out[fn] = await stage.page.evaluate("""([u, fn, pause, resume]) => new Promise((ok) => {
                    let done = false;
                    __lecturer[fn](u).then(() => { done = true; });
                    __lecturer[pause]();
                    setTimeout(() => {
                      const early = done;
                      __lecturer[resume]();
                      setTimeout(() => ok([early, done]), 4000);
                    }, 1000);
                })""", [url, fn, pause, resume])
            await stage.close()
            return out

    out = asyncio.run(go())
    assert out == {"play": [False, True], "playAside": [False, True]}  # 暂停时没算播完；继续后播完
