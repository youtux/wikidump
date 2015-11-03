def assert_captures_in_text(captures, text):
    for _, (capture_begin, capture_end) in captures:
        assert 0 <= capture_begin <= len(text)
        assert 0 <= capture_end <= len(text)
