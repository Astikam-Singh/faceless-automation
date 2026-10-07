import os
from datetime import datetime
from src.script_generator import ScriptGenerator
from src.tts import TextToSpeech
from src.assets import AssetFetcher
from src.renderer import VideoRenderer
from src.clip_processor import ClipProcessor
from src.publishers.youtube import YouTubePublisher
from src.publishers.instagram import InstagramPublisher

def run_shortform():
    print("=== Starting Short-form Pipeline (45-60 secs) ===")
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    script_gen = ScriptGenerator()
    script = script_gen.generate_script(is_longform=False)
    filename_base = f"output/{run_id}_short"

    tts = TextToSpeech()
    segments = [s for s in script.get('segments', []) if isinstance(s, dict) and 'text' in s]
    audio_path = tts.generate_voiceover(segments, output_path=f"{filename_base}_audio.mp3")
    
    fetcher = AssetFetcher()
    clips = []
    for i, s in enumerate(segments):
        query = s.get('visual_prompt', s.get('text', 'minimalist aesthetic'))
        path = fetcher.fetch_video(query, f"output/clip_short_{i}.mp4")
        if path: clips.append(ClipProcessor().process_clip(path, i, is_longform=False))
    
    renderer = VideoRenderer(is_longform=False)
    video_path = renderer.render(audio_path, clips, f"{filename_base}.mp4")
    
    # Publish to YouTube Shorts and Instagram Reels
    YouTubePublisher().upload_video(script, video_path)
    ig_pub = InstagramPublisher()
    if ig_pub.is_ready(): ig_pub.upload_reel(script, video_path)

if __name__ == "__main__":
    run_shortform()
