import os
import json
from src.script_generator import ScriptGenerator
from src.tts import TextToSpeech
from src.assets import AssetFetcher
from src.renderer import VideoRenderer
from src.video_formatter import VideoFormatter
from src.publishers.youtube import YouTubePublisher
from src.publishers.instagram import InstagramPublisher

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
    
    # 1. Generate Script
    print("\n[1/6] Generating viral script via Gemini...")
    script_gen = ScriptGenerator()
    script_data = script_gen.generate_script()
    print(f"Title: {script_data.get('title')}")
    
    full_text = " ".join([seg['text'] for seg in script_data.get('segments', [])])
    
    # 2. Generate Voiceover
    print("\n[2/6] Generating neural voiceover via Edge-TTS...")
    tts = TextToSpeech()
    audio_path = tts.generate_voiceover(full_text)
    print(f"Audio ready at {audio_path}")
    
    # 3. Fetch Visual Assets
    print("\n[3/6] Fetching B-roll assets...")
    fetcher = AssetFetcher()
    segments = script_data.get('segments', [])
    for i, seg in enumerate(segments):
        prompt = seg.get('visual_prompt', 'cinematic dark aesthetic')
        fetcher.fetch_video(prompt, f"output/clip_{i}.mp4")
        
    # 4. Render Base Video
    print("\n[4/6] Rendering base video with branding...")
    renderer = VideoRenderer()
    base_video = renderer.render(audio_path, segments)
    print(f"Base video ready: {base_video}")
    
    # Generate thumbnail
    print("\n[Generating thumbnail...]")
    thumbnail_gen = ThumbnailGenerator()
    title = script_data.get('title', 'Ancient Wisdom')
    thumbnail_path = thumbnail_gen.generate_from_video(base_video, title)
    if thumbnail_path:
        print(f"✅ Thumbnail generated: {thumbnail_path}")
    
    # 5. Create Multi-Format Videos
    print("\n[5/6] Creating multi-format videos...")
    formatter = VideoFormatter()
    
    longform_video = None
    if os.path.exists(base_video):
        if os.path.getsize(base_video) > 1024 * 1024:  # At least 1MB
            # Create long-form YouTube video (10-12 mins)
            longform_video = formatter.create_longform_video(base_video)
            print(f"Long-form video ready: {longform_video}")
            
            # Create short-form for Reels/Shorts (45-60 secs)
            shortform_video = formatter.create_shortform_video(base_video, max_duration=60)
            print(f"Short-form video ready: {shortform_video}")
        else:
            print("⚠ Base video too small for format conversion")
    
    # 6. Auto-Publish to Social Media
    print("\n[6/6] Auto-publishing to social platforms...")
    
    # Publish to YouTube
    youtube_pub = YouTubePublisher()
    if os.path.exists(base_video):
        yt_result = youtube_pub.upload_video(script_data, base_video)
        if yt_result:
            print(f"✅ YouTube upload successful: {yt_result.get('video_url', 'N/A')}")
    
    # Publish to Instagram
    ig_pub = InstagramPublisher()
    if ig_pub.is_ready():
        ig_result = ig_pub.upload_reel(script_data, base_video)
        if ig_result:
            print(f"✅ Instagram Reels upload successful: {ig_result.get('upload_url', 'N/A')}")
    else:
        print("⚠ Instagram publishing skipped: token/account_id not configured")
    
    # Cleanup old files
    print("\n[7/7] Checking disk cleanup...")
    cleanup_old_files()
    
    print(f"\n✨ Pipeline complete! Videos ready at output/")
    print(f"   - Base video: {base_video}")
    if longform_video:
        print(f"   - Long-form: {longform_video}")
    if shortform_video:
        print(f"   - Short-form: {shortform_video}")

if __name__ == "__main__":
    main()
