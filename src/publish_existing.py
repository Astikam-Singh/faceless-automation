import os
import glob
from src.publishers.youtube import YouTubePublisher
from src.publishers.instagram import InstagramPublisher
from src.thumbnail import ThumbnailGenerator
from src.qa_engine import QAEngine
import yaml

def publish_latest():
    output_dir = "output"
    
    # Updated to be more flexible, finding any mp4s if the specific suffixes fail
    longform = glob.glob(os.path.join(output_dir, "*longform.mp4"))
    if not longform: longform = glob.glob(os.path.join(output_dir, "final_video.mp4"))
    
    shortform = glob.glob(os.path.join(output_dir, "*shortform.mp4"))
    if not shortform: shortform = glob.glob(os.path.join(output_dir, "final_video.mp4"))
    
    thumbnail = glob.glob(os.path.join(output_dir, "*thumbnail.jpg"))
    
    # Get latest based on mtime
    latest_long = max(longform, key=os.path.getmtime) if longform else None
    latest_short = max(shortform, key=os.path.getmtime) if shortform else None
    latest_thumb = max(thumbnail, key=os.path.getmtime) if thumbnail else None
    
    print(f"Found latest files:\n - Long: {latest_long}\n - Short: {latest_short}\n - Thumbnail: {latest_thumb}")
    
    if not latest_long or not latest_short:
        print("âŒ Could not find generated long-form or short-form videos.")
        return
        
    # Mock script data (In a real scenario, this should be persisted)
    script_data = {
        'title': 'The Stoic Paradox',
        'description': 'Ancient wisdom for modern challenges.',
        'hashtags': ['#stoicism', '#mindset']
    }
    
    # QA Check
    print("\n[QA Check]...")
    qa = QAEngine()
    # Note: Requires audio_path, will just use placeholder audio if not strictly required or use latest found.
    success_rate = qa.analyze_video(latest_long)
    print(f"ðŸ“Š Video QA Score: {success_rate*100:.1f}%")
    
    if success_rate >= 0.85:
        # Thumbnail Generation
        thumbnail_gen = ThumbnailGenerator()
        thumbnail_path = thumbnail_gen.generate_from_video(latest_long, script_data['title'])
        
        # Publish
        yt_pub = YouTubePublisher()
        yt_result = yt_pub.upload_video(script_data, latest_long, thumbnail_path=thumbnail_path)
        
        ig_pub = InstagramPublisher()
        ig_result = ig_pub.upload_reel(script_data, latest_short)
        
        print("âœ¨ Publishing sequence complete.")
    else:
        print("âŒ QA Failed. Cannot publish.")

if __name__ == "__main__":
    publish_latest()
