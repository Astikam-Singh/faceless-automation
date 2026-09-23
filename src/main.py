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
from src.publishers.instagram import InstagramPublisher
from src.qa_engine import QAEngine
import time
from multiprocessing.pool import ThreadPool

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
    print("=== Starting Ancient Mindset Lab Production Pipeline ===")
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    max_attempts = 3
    for attempt in range(max_attempts):
        print(f"\n--- Pipeline Attempt {attempt + 1}/{max_attempts} ---")
        
        # 1. Generate Scripts
        print("\n[1/7] Generating unique viral scripts...")
        script_gen = ScriptGenerator()
        long_script = script_gen.generate_script(is_longform=True)
        short_script = script_gen.generate_script(is_longform=False)
        filename_base = f"output/{run_id}_{attempt}"
        
        # 2. Generate Voiceovers
        print("\n[2/7] Generating voiceovers...")
        tts = TextToSpeech()
        audio_long = tts.generate_voiceover(long_script['segments'], output_path=f"{filename_base}_long_audio.mp3")
        audio_short = tts.generate_voiceover(short_script['segments'], output_path=f"{filename_base}_short_audio.mp3")
        
        # 3. Fetch Visual Assets
        print("\n[3/7] Fetching unique assets...")
        fetcher = AssetFetcher()
        long_raw = [fetcher.fetch_video(s['visual_prompt'], f"output/clip_long_{i}.mp4") for i, s in enumerate(long_script.get('segments', []))]
        short_raw = [fetcher.fetch_video(s['visual_prompt'], f"output/clip_short_{i}.mp4") for i, s in enumerate(short_script.get('segments', []))]
        
        # 4. Process Clips
        long_clips = [ClipProcessor().process_clip(c, i, is_longform=True) for i, c in enumerate(long_raw) if c]
        short_clips = [ClipProcessor().process_clip(c, i, is_longform=False) for i, c in enumerate(short_raw) if c]
        
        # 5. Render
        print("\n[5/7] Rendering...")
        with ThreadPool(processes=2) as pool:
            ar_long = pool.apply_async(VideoRenderer(is_longform=True).render, (audio_long, long_clips, f"{filename_base}_longform.mp4"))
            ar_short = pool.apply_async(VideoRenderer(is_longform=False).render, (audio_short, short_clips, f"{filename_base}_shortform.mp4"))
            longform_video = ar_long.get()
            shortform_video = ar_short.get()
        
        # 6. QA
        print("\n[6/7] Running QA...")
        qa = QAEngine()
        success = qa.run_qa(longform_video, audio_long, " ".join([s['text'] for s in long_script.get('segments', [])]))
        
        if success >= 0.85:
            # Thumbnail & Publish
            thumb_path = ThumbnailGenerator().generate_from_video(longform_video, long_script['title'], output_path=f"{filename_base}_thumbnail.jpg")
            
            # Auto-Publish
            print("\n[7/7] Auto-publishing...")
            youtube_pub = YouTubePublisher()
            if os.path.exists(longform_video): youtube_pub.upload_video(long_script, longform_video, thumbnail_path=thumb_path)
            youtube_pub.upload_video(short_script, shortform_video)
            
            ig_pub = InstagramPublisher()
            if ig_pub.is_ready(): ig_pub.upload_reel(short_script, shortform_video)
            break
        else:
            print(f"⚠️ Attempt {attempt + 1} failed QA ({success*100:.1f}%). Retrying...")
    else:
        print(f"\n❌ Pipeline failed after {max_attempts} attempts.")
        return
    
    # Cleanup old files
    print("\n[7/7] Checking disk cleanup...")
    cleanup_old_files()
    
    print(f"\n✨ Pipeline complete! Videos ready at output/")
    print(f"   - Long-form: {longform_video}")
    print(f"   - Short-form: {shortform_video}")

if __name__ == "__main__":
    main()
