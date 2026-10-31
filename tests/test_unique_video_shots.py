from src.assets import AssetFetcher
from src.clip_processor import ClipProcessor
from src.renderer import VideoRenderer


def test_asset_ids_are_reserved_across_fetcher_instances(tmp_path):
    history_path = tmp_path / "used_videos.json"
    first_fetcher = AssetFetcher(history_path=str(history_path))
    second_fetcher = AssetFetcher(history_path=str(history_path))

    assert first_fetcher._reserve_asset_id("pexels-123") is True
    assert second_fetcher._reserve_asset_id("pexels-123") is False
    assert second_fetcher._reserve_asset_id("pexels-456") is True


def test_asset_selection_prefers_resolution_near_output_size():
    video_files = [
        {"width": 1280, "height": 720, "link": "720p.mp4"},
        {"width": 1920, "height": 1080, "link": "1080p.mp4"},
        {"width": 3840, "height": 2160, "link": "4k.mp4"},
    ]

    selected = AssetFetcher._select_video_file(video_files, "landscape")

    assert selected["link"] == "1080p.mp4"


def test_asset_selection_uses_height_for_portrait():
    video_files = [
        {"width": 1080, "height": 1920, "link": "1080x1920.mp4"},
        {"width": 2160, "height": 3840, "link": "4k-portrait.mp4"},
    ]

    selected = AssetFetcher._select_video_file(video_files, "portrait")

    assert selected["link"] == "1080x1920.mp4"


def test_clip_processor_trims_sources_to_six_seconds(monkeypatch):
    commands = []

    def capture_command(command, check):
        commands.append(command)

    monkeypatch.setattr("src.clip_processor.subprocess.run", capture_command)
    processor = ClipProcessor()

    processor.process_clip("long-source.mp4", 999, is_longform=True)

    command = commands[0]
    assert command[command.index("-t") + 1] == "6"
    assert command[command.index("-preset") + 1] == "veryfast"


def test_renderer_rejects_shots_longer_than_six_seconds():
    try:
        VideoRenderer._shot_duration(61, 10)
    except ValueError as error:
        assert "unique clips" in str(error)
    else:
        raise AssertionError("Renderer accepted shots longer than six seconds")


def test_renderer_reads_source_durations_one_clip_at_a_time(monkeypatch):
    active_readers = 0
    maximum_readers = 0

    class FakeClip:
        duration = 6

        def close(self):
            nonlocal active_readers
            active_readers -= 1

    def open_clip(_path):
        nonlocal active_readers, maximum_readers
        active_readers += 1
        maximum_readers = max(maximum_readers, active_readers)
        return FakeClip()

    monkeypatch.setattr("src.renderer.VideoFileClip", open_clip)

    durations = VideoRenderer._get_source_durations(["first.mp4", "second.mp4", "third.mp4"])

    assert durations == [6, 6, 6]
    assert maximum_readers == 1
    assert active_readers == 0


def test_renderer_uses_five_second_shots_when_enough_clips_exist():
    assert VideoRenderer._shot_duration(61, 13) <= 5


def test_short_source_shot_is_compensated_by_other_unique_shots():
    durations = VideoRenderer._allocate_shot_durations(
        audio_duration=61,
        source_durations=[3.5] + [6.0] * 11,
    )

    assert abs(sum(durations) - 61) < 0.01
    assert durations[0] == 3.5
    assert all(0 < duration <= 6 for duration in durations)


def test_renderer_rejects_insufficient_unique_footage():
    try:
        VideoRenderer._allocate_shot_durations(61, [3.5] * 10)
    except ValueError as error:
        assert "Fetch more unique clips" in str(error)
    else:
        raise AssertionError("Renderer accepted insufficient unique footage")