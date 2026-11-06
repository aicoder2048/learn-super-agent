import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from course import parse_args  # noqa: E402


def test_defaults_to_course_only_on_8766():
    a = parse_args([])
    assert a.port == 8766 and a.lecture is None


def test_positional_port_still_works():
    assert parse_args(["9999"]).port == 9999


def test_port_flag():
    assert parse_args(["--port", "9999"]).port == 9999


def test_lecture_with_lesson_and_start():
    a = parse_args(["--lecture", "sa02", "--port", "9999", "--from", "s3"])
    assert (a.lecture, a.port, a.start) == ("SA02", 9999, "s3")


def test_from_requires_lecture():
    with pytest.raises(SystemExit):
        parse_args(["--from", "s3"])


def test_conflicting_ports_rejected():
    with pytest.raises(SystemExit):
        parse_args(["9000", "--port", "9999"])
