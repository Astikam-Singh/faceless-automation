from src.thumbnail import ThumbnailGenerator
from src.script_generator import ScriptGenerator


def test_fallback_thumbnail_hook_drops_brand_prefix_and_limits_words():
    hook = ThumbnailGenerator._thumbnail_copy(
        "Ancient Mindset Lab | Stop Letting Anger Control You Today"
    )

    assert hook == "Stop Letting Anger Control"
    assert len(hook.split()) == 4


def test_packaging_removes_brand_prefix_and_preserves_bold_hook():
    script = {
        "title": "Ancient Mindset Lab | Master Your Anger and Stay Unshaken",
        "thumbnail_text": "NEVER LET ANGER CONTROL YOU",
    }

    normalized = ScriptGenerator._normalize_packaging(script, "Ancient Mindset Lab")

    assert normalized["title"] == "Master Your Anger and Stay Unshaken"
    assert normalized["thumbnail_text"] == "NEVER LET ANGER CONTROL YOU"