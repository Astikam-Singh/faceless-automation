import os
import json
from datetime import datetime
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
    audio_path = tts.generate_voiceover(segments, output_path=f"{filename_base}_audio.mp3")
    
    fetcher = AssetFetcher()
    clips = []
    for i, s in enumerate(segments):
        query = s.get('visual_prompt', s.get('text', 'minimalist stoic aesthetic'))
        path = fetcher.fetch_video(query, f"output/clip_long_{i}.mp4")
        if path: clips.append(ClipProcessor().process_clip(path, i, is_longform=True))
    
    renderer = VideoRenderer(is_longform=True)
    video_path = renderer.render(audio_path, clips, f"{filename_base}.mp4")
    
    qa = QAEngine()
    text_content = " ".join([s.get('text', '') for s in segments])
    success_score = qa.run_qa(video_path, audio_path, text_content)
    print(f"DEBUG: Longform QA Score: {success_score}")
    
    if success_score >= 0.85:
        thumb = ThumbnailGenerator().generate_from_video(video_path, script['title'], output_path=f"{filename_base}_thumb.jpg")
        YouTubePublisher().upload_video(script, video_path, thumbnail_path=thumb)
    else:
        print(f"❌ Longform QA Failed with score: {success_score}")
    
if __name__ == "__main__":
    run_longform()
