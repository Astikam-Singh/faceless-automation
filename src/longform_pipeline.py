import os
import json
from datetime import datetime
from moviepy.editor import AudioFileClip
from src.script_generator import ScriptGenerator
from src.tts import TextToSpeech
from src.assets import AssetFetcher
from src.renderer import VideoRenderer
from src.thumbnail import ThumbnailGenerator
from src.clip_processor import ClipProcessor
from src.publishers.youtube import YouTubePublisher
from src.qa_engine import QAEngine

def run_longform():
    print("=== Starting Long-form Pipeline (10-20 mins) ===")
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    script_gen = ScriptGenerator()
    script = script_gen.generate_script(is_longform=True)
    filename_base = f"output/{run_id}_long"

    tts = TextToSpeech()
    segments = [s for s in script.get('segments', []) if isinstance(s, dict) and 'text' in s]
    audio_path = tts.generate_voiceover(segments, output_path=f"{filename_base}_audio.wav")
    if not audio_path:
        raise RuntimeError("Long-form voiceover generation failed; stopping before video rendering.")

    audio_clip = AudioFileClip(audio_path)
    audio_duration = audio_clip.duration
    audio_clip.close()
    fetcher = AssetFetcher()
    raw_clips = fetcher.fetch_video_shots(
        segments,
        audio_duration,
        f"{filename_base}_raw",
        orientation="landscape",
        shot_seconds=5,
    )
    processor = ClipProcessor()
    clips = [
        processor.process_clip(path, i, is_longform=True)
        for i, path in enumerate(raw_clips)
    ]
    
    renderer = VideoRenderer(is_longform=True)
    video_path = renderer.render(audio_path, clips, f"{filename_base}.mp4")
    
    qa = QAEngine()
    text_content = " ".join([s.get('text', '') for s in segments])
    success_score = qa.run_qa(video_path, audio_path, text_content)
    print(f"DEBUG: Longform QA Score: {success_score}")
    
    threshold = 0.8
    if success_score >= threshold:
        print(f"✅ QA Passed ({success_score*100:.1f}%), proceeding to publish...")
        thumb = ThumbnailGenerator().generate_from_video(
            video_path,
            script['title'],
            output_path=f"{filename_base}_thumb.jpg",
            thumbnail_text=script.get('thumbnail_text'),
        )
        YouTubePublisher().upload_video(script, video_path, thumbnail_path=thumb)
    else:
        print(f"❌ Longform QA Failed: Score {success_score:.2f} is below threshold {threshold}. Video not published.")
    
if __name__ == "__main__":
    run_longform()
