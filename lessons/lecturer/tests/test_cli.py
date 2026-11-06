import pytest

from lecturer import course_url


def test_course_url_uses_port():
    assert course_url(9000) == "http://127.0.0.1:9000/lessons/"


def test_course_url_rejects_bad_port():
    with pytest.raises(SystemExit):
        course_url(70000)
