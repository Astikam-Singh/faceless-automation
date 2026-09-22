import os
import json
from datetime import datetime
from src.script_generator import ScriptGenerator
from src.tts import TextToSpeech
from src.assets import AssetFetcher
from src.renderer import VideoRenderer
from src.thumbnail import ThumbnailGenerator
from src.video_formatter import VideoFormatter
from src.publishers.youtube import YouTubePublisher
from src.publishers.instagram import InstagramPublisher
from src.qa_engine import QAEngine
import time

def cleanup_old_files(config_path="config.yaml"):
    """Auto-cleanup old output files to prevent disk space issues."""
    import yaml
    import time
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.load(f, Loader=yaml.SafeLoader)
    
    output_dir = "output"
    if not os.path.exists(output_dir):
        return
    
    cleanup_days = config.get('output', {}).get('cleanup_older_than_days', 7)
    max_age_seconds = cleanup_days * 24 * 60 * 60
    
    current_time = time.time()
    deleted_count = 0
    deleted_size = 0
    
    for filename in os.listdir(output_dir):
        filepath = os.path.join(output_dir, filename)
        if os.path.isfile(filepath):
            file_age = current_time - os.path.getmtime(filepath)
            if file_age > max_age_seconds:
                try:
                    size = os.path.getsize(filepath)
                    os.remove(filepath)
                    deleted_count += 1
                    deleted_size += size
                except Exception as e:
                    print(f"  Could not delete {filename}: {e}")
    
    if deleted_count > 0:
        print(f"  ✅ Cleanup complete: Removed {deleted_count} files ({deleted_size/1024/1024:.2f} MB)")

def main():
    print("=== Starting Ancient Mindset Lab Video Pipeline ===")
    
    # 0. Generate Unique Run ID
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # QA & Iteration Loop
    max_attempts = 3
    for attempt in range(max_attempts):
        print(f"\n--- Pipeline Attempt {attempt + 1}/{max_attempts} ---")
        
        # 1. Generate Script (Long-form request)
        print("\n[1/6] Generating viral long-form script via Gemini...")
        script_gen = ScriptGenerator()
        script_data = script_gen.generate_script(is_longform=True)
        title = script_data.get('title', 'Stoic_Wisdom').replace(" ", "_").replace("|", "_")[:50]
        filename_base = f"output/{run_id}_{attempt}_{title}"
        print(f"Title: {script_data.get('title')}")
        
        segments = script_data.get('segments', [])
        print(f"DEBUG: Generated {len(segments)} segments.")
        
        full_text = " ".join([seg['text'] for seg in segments])
        
        # 2. Generate Voiceover
        print("\n[2/6] Generating neural voiceover via Edge-TTS...")
        tts = TextToSpeech()
        audio_path = tts.generate_voiceover(script_data['segments'])
        print(f"Audio ready at {audio_path}")
        
        # 3. Fetch Visual Assets
        print("\n[3/6] Fetching B-roll assets...")
        fetcher = AssetFetcher()
        for i, seg in enumerate(segments):
            prompt = seg.get('visual_prompt', 'cinematic dark aesthetic')
            fetcher.fetch_video(prompt, f"output/clip_{i}.mp4")
            
        # 4. Render Video Formats
        print("\n[4/6] Rendering formats (Long-form & Short-form)...")
        renderer_long = VideoRenderer(is_longform=True)
        longform_video = renderer_long.render(audio_path, segments, output_path=f"{filename_base}_longform.mp4")
        
        renderer_short = VideoRenderer(is_longform=False)
        shortform_video = renderer_short.render(audio_path, segments, output_path=f"{filename_base}_shortform.mp4")
        
        # 5. Quality Assurance
        print("\n[5/6] Running automated Quality Assurance check...")
        qa = QAEngine()
        success_rate = qa.run_qa(longform_video, audio_path, full_text)
        
        if success_rate >= 0.85:
            print(f"✅ QA passed on attempt {attempt + 1}!")
            
            # Generate thumbnail
            print("\n[Generating thumbnail...]")
            thumbnail_gen = ThumbnailGenerator()
            thumbnail_path = thumbnail_gen.generate_from_video(longform_video, script_data.get('title', 'Stoic Wisdom'), output_path=f"{filename_base}_thumbnail.jpg")
            
            # 6. Auto-Publish to Social Media
            print("\n[6/6] Auto-publishing to social platforms...")
            
            # Publish to YouTube (Longform)
            youtube_pub = YouTubePublisher()
            if os.path.exists(longform_video):
                yt_result = youtube_pub.upload_video(script_data, longform_video, thumbnail_path=thumbnail_path)
                if yt_result:
                    print(f"✅ YouTube upload successful: {yt_result.get('video_url', 'N/A')}")
            
            # Publish to Instagram (Shortform)
            ig_pub = InstagramPublisher()
            if ig_pub.is_ready():
                ig_result = ig_pub.upload_reel(script_data, shortform_video)
                if ig_result:
                    print(f"✅ Instagram Reels upload successful: {ig_result.get('upload_url', 'N/A')}")
            else:
                print("⚠ Instagram publishing skipped: token/account_id not configured")
            
            # Break loop on success
            break
        else:
            print(f"⚠️ Attempt {attempt + 1} failed QA ({success_rate*100:.1f}%). Retrying...")
    else:
        print(f"\n❌ Pipeline failed after {max_attempts} attempts.")
        return
    
    # Cleanup old files
    print("\n[7/7] Checking disk cleanup...")
    cleanup_old_files()
    
    print(f"\n✨ Pipeline complete! Videos ready at output/")
    print(f"   - Long-form: {longform_video}")
    print(f"   - Short-form: {shortform_video}")
