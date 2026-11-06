import pytest

from lecturer import course_url


def test_course_url_uses_port():
    assert course_url(9000) == "http://127.0.0.1:9000/lessons/"


def test_course_url_rejects_bad_port():
    with pytest.raises(SystemExit):
        course_url(70000)


def test_lesson_sequence_from_given_lesson(tmp_path):
    from lecturer import lesson_sequence

    for n in ("SA01", "SA02", "SA03"):
        (tmp_path / f"{n}.json").write_text("{}")
    assert lesson_sequence("sa02", tmp_path) == ["SA02", "SA03"]


def test_lesson_sequence_unknown_lesson(tmp_path):
    from lecturer import lesson_sequence
    from script import ScriptError

    (tmp_path / "SA01.json").write_text("{}")
    with pytest.raises(ScriptError, match="SA05"):
        lesson_sequence("SA05", tmp_path)
