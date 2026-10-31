from src.thumbnail import ThumbnailGenerator


def test_fallback_thumbnail_hook_drops_brand_prefix_and_limits_words():
    hook = ThumbnailGenerator._thumbnail_copy(
        "Ancient Mindset Lab | Stop Letting Anger Control You Today"
    )

    assert hook == "Stop Letting Anger Control"
    assert len(hook.split()) == 4