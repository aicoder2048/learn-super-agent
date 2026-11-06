from tts import SentenceStream, audio_name, clean_text, split_sentences


def test_audio_name_is_stable_and_voice_specific():
    a = audio_name("v1", "你好。")
    assert a == audio_name("v1", "你好。")
    assert a != audio_name("v2", "你好。")


def test_clean_text_strips_markdown():
    assert clean_text("**结论**：用 `Router`。\n- 第一点") == "结论：用 Router。 第一点"


def test_split_sentences_on_chinese_punctuation():
    assert split_sentences("先说结论。为什么？因为快！") == ["先说结论。", "为什么？", "因为快！"]


def test_split_sentences_merges_tiny_fragments():
    assert split_sentences("好。我们继续看下一张图。") == ["好。我们继续看下一张图。"]


def test_stream_yields_only_new_complete_sentences():
    s = SentenceStream()
    assert s.feed("第一句话说完了。第二句") == ["第一句话说完了。"]
    assert s.feed("第一句话说完了。第二句也说完了。第三") == ["第二句也说完了。"]
    assert s.flush() == ["第三"]


def test_stream_flush_empty_when_nothing_left():
    s = SentenceStream()
    s.feed("一句完整的话。")
    assert s.flush() == []
