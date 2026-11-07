"""学生提问的回答在朗读时：空格暂停/继续朗读，Esc 停止朗读。"""

import asyncio

from controls import Controls
from player import Lecture
from script import Script, Step


class FakeStage:
    def __init__(self):
        self.notes, self.calls = [], []

    async def status(self, html, paused, can_reexplain):
        self.notes.append((html, paused))

    async def pause_aside(self):
        self.calls.append("pause_aside")

    async def resume_aside(self):
        self.calls.append("resume_aside")

    async def stop_aside(self):
        self.calls.append("stop_aside")


def reading_lecture():
    step = Step(id="s1-01", section="s1", kind="say", target="h2", say="hi")
    stage = FakeStage()
    lec = Lecture(Script("X.html", "X", [step]), stage, Controls())
    lec.controls.pause()  # 学生提问时讲课已自动暂停
    return lec, stage


async def start_reading(lec):
    lec.reading = asyncio.create_task(asyncio.Event().wait())  # 一段还没读完的朗读


def test_space_pauses_reading_without_cancelling_it():
    lec, stage = reading_lecture()

    async def go():
        await start_reading(lec)
        await lec.on_command("toggle")
        assert stage.calls == ["pause_aside"]
        assert lec.reading and not lec.reading.done()
        assert "空格继续" in stage.notes[-1][0] and stage.notes[-1][1] is True
        lec.reading.cancel()

    asyncio.run(go())


def test_second_space_resumes_reading():
    lec, stage = reading_lecture()

    async def go():
        await start_reading(lec)
        await lec.on_command("toggle")
        await lec.on_command("toggle")
        assert stage.calls == ["pause_aside", "resume_aside"]
        assert lec.reading_on.is_set() and not lec.reading.done()
        assert lec.controls.paused  # 讲课仍然暂停
        lec.reading.cancel()

    asyncio.run(go())


def test_escape_stops_reading_and_keeps_lecture_paused():
    lec, stage = reading_lecture()

    async def go():
        await start_reading(lec)
        await lec.on_command("toggle")
        await lec.on_command("stop")
        assert lec.reading is None and "stop_aside" in stage.calls
        assert lec.controls.paused and lec.reading_on.is_set()
        assert "空格继续讲课" in stage.notes[-1][0]

    asyncio.run(go())


def test_reading_note_mentions_space_and_escape():
    lec, stage = reading_lecture()

    async def go():
        await start_reading(lec)
        await lec.show()
        lec.reading.cancel()

    asyncio.run(go())
    html, paused = stage.notes[-1]
    assert "<b>助教</b>" in html and "空格暂停" in html and "Esc" in html and paused is False


# ---------- 认出学生的新提问 ----------
class WatchStage(FakeStage):
    """tutor_last 依次返回（助教回答条数，最后一条回答的 id），用完后停在最后一个状态。"""

    def __init__(self, states):
        super().__init__()
        self.states = list(states)

    async def tutor_last(self):
        return self.states.pop(0) if len(self.states) > 1 else self.states[0]

    async def pause_audio(self):
        self.calls.append("pause_audio")


def watch(states, polls=8):
    step = Step(id="s1-01", section="s1", kind="say", target="h2", say="hi")
    lec = Lecture(Script("X.html", "X", [step]), WatchStage(states), Controls())
    lec.poll = 0.01
    read = []

    async def fake_read(index, aside=False):
        read.append(index)
    lec.speak_tutor_answer = fake_read

    async def go():
        task = asyncio.create_task(lec.watch_student_questions())
        await asyncio.sleep(lec.poll * polls)
        task.cancel()
    asyncio.run(go())
    return read, lec


def test_new_question_is_read():
    read, lec = watch([(1, "a"), (1, "a"), (2, "b")])
    assert read == [1] and lec.controls.paused


def test_resend_keeps_count_but_is_still_read():
    # 「重新发送」删掉出错的一问一答再问：条数不变，最后一条换了 id
    read, _ = watch([(2, "b"), (2, "b"), (2, "c")])
    assert read == [1]


def test_cleared_then_asked_again_is_read():
    read, _ = watch([(3, "c"), (0, ""), (1, "d")])
    assert read == [0]


def test_nothing_new_reads_nothing():
    read, _ = watch([(2, "b")])
    assert read == []


def test_answers_during_proxy_question_are_not_read():
    step = Step(id="s1-01", section="s1", kind="say", target="h2", say="hi")
    lec = Lecture(Script("X.html", "X", [step]), WatchStage([(1, "a"), (2, "p")]), Controls())
    lec.poll, read = 0.01, []

    async def fake_read(index, aside=False):
        read.append(index)
    lec.speak_tutor_answer = fake_read

    async def go():
        task = asyncio.create_task(lec.watch_student_questions())
        await asyncio.sleep(0.005)
        lec.proxy_active = True        # 讲师代问：回答由讲师自己读
        await asyncio.sleep(0.05)
        lec.seen_answer, lec.proxy_active = "p", False
        await asyncio.sleep(0.05)
        task.cancel()
    asyncio.run(go())
    assert read == []
