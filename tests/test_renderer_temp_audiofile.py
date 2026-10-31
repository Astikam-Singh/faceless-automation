import inspect

from moviepy.editor import VideoClip


def test_moviepy_temp_audiofile_keyword_is_supported():
    params = inspect.signature(VideoClip.write_videofile).parameters
    assert "temp_audiofile" in params
    assert "TEMP_AUDIOFILE" not in params
