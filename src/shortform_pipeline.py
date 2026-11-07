import os
from moviepy.editor import AudioFileClip
from datetime import datetime
from src.script_generator import ScriptGenerator
from src.tts import TextToSpeech
from src.assets import AssetFetcher
from src.renderer import VideoRenderer
from src.clip_processor import ClipProcessor
from src.publishers.youtube import YouTubePublisher
from src.publishers.instagram import InstagramPublisher
from src.publishers.facebook import FacebookPublisher

def run_shortform():
    print("=== Starting Short-form Pipeline (45-60 secs) ===")
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    script_gen = ScriptGenerator()
    script = script_gen.generate_script(is_longform=False)
    filename_base = f"output/{run_id}_short"

    tts = TextToSpeech()
    segments = [s for s in script.get('segments', []) if isinstance(s, dict) and 'text' in s]
    audio_path = tts.generate_voiceover(segments, output_path=f"{filename_base}_audio.wav")
    if not audio_path:
        raise RuntimeError("Short-form voiceover generation failed; stopping before video rendering.")

    audio_clip = AudioFileClip(audio_path)
    audio_duration = audio_clip.duration
    audio_clip.close()
    fetcher = AssetFetcher()
    raw_clips = fetcher.fetch_video_shots(
        segments,
        audio_duration,
        f"{filename_base}_raw",
        orientation="portrait",
        shot_seconds=5,
    )
    processor = ClipProcessor()
    clips = [
        processor.process_clip(path, i, is_longform=False)
        for i, path in enumerate(raw_clips)
    ]
    
    renderer = VideoRenderer(is_longform=False)
    video_path = renderer.render(audio_path, clips, f"{filename_base}.mp4")
    
    # Publish to YouTube Shorts, Instagram Reels, and Facebook Reels
    YouTubePublisher().upload_video(script, video_path)
    ig_pub = InstagramPublisher()
    if ig_pub.is_ready(): ig_pub.upload_reel(script, video_path)
    fb_pub = FacebookPublisher()
    if fb_pub.is_ready(): fb_pub.upload_reel(script, video_path)

if __name__ == "__main__":
    run_shortform()
