import json

import pytest

from lecturer import course_url, default_port, lesson_sequence
from script import ScriptError


def test_course_url_uses_port_and_lessons_dir():
    assert course_url(9000, "lessons") == "http://127.0.0.1:9000/lessons/"


def test_course_url_rejects_bad_port():
    with pytest.raises(SystemExit):
        course_url(70000)


def test_default_port_comes_from_sources_json(tmp_path):
    m = tmp_path / "sources.json"
    m.write_text(json.dumps({"course": {"port": 9123}}))
    assert default_port(m) == 9123


def test_default_port_falls_back_without_manifest(tmp_path):
    assert default_port(tmp_path / "nope.json") == 8766


def test_lesson_sequence_from_given_lesson(tmp_path):
    for n in ("L01", "L02", "L03"):
        (tmp_path / f"{n}.json").write_text("{}")
    assert lesson_sequence("l02", tmp_path) == ["L02", "L03"]


def test_lesson_sequence_unknown_lesson(tmp_path):
    (tmp_path / "L01.json").write_text("{}")
    with pytest.raises(ScriptError, match="L05"):
        lesson_sequence("L05", tmp_path)
