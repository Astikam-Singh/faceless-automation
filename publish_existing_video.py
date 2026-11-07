import os
import json
from src.publishers.youtube import YouTubePublisher
from src.publishers.instagram import InstagramPublisher
from src.publishers.facebook import FacebookPublisher

def publish_existing_video(video_path, script_data=None):
    """
    Publish an already created video to all platforms.
    
    Args:
        video_path: Path to the video file
        script_data: Optional dict with title, description, etc. If None, generates placeholder data.
    """
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return
    
    # Generate script data if not provided
    if script_data is None:
        filename = os.path.basename(video_path)
        script_data = {
            'title': f"Stoic Wisdom: {filename}",
            'description': f"A Stoic philosophy video.\n\n#Stoicism #Mindset #Philosophy",
            'tags': ["Stoicism", "Mindset", "Philosophy", "SelfImprovement"]
        }
    
    print(f"\n=== Publishing Video: {video_path} ===")
    print(f"Title: {script_data.get('title', 'Unknown')}")
    
    # Get video file info
    file_size = os.path.getsize(video_path) / (1024 * 1024)
    print(f"Video size: {file_size:.2f} MB")
    
    # Publish to YouTube
    print("\n--- Publishing to YouTube ---")
    try:
        yt_pub = YouTubePublisher()
        if yt_pub.youtube:  # Check if authenticated
            yt_response = yt_pub.upload_video(script_data, video_path)
            print(f"YouTube upload response: {yt_response}")
        else:
            print("⚠ YouTube authentication failed")
    except Exception as e:
        print(f"⚠ YouTube publishing not configured or failed: {e}")
    
    # Publish to Instagram
    print("\n--- Publishing to Instagram ---")
    ig_pub = InstagramPublisher()
    if ig_pub.is_ready():
        ig_response = ig_pub.upload_reel(script_data, video_path)
        print(f"Instagram upload response: {ig_response}")
    else:
        print("⚠ Instagram publishing not configured")
    
    # Publish to Facebook
    print("\n--- Publishing to Facebook ---")
    fb_pub = FacebookPublisher()
    if fb_pub.is_ready():
        fb_response = fb_pub.upload_reel(script_data, video_path)
        print(f"Facebook upload response: {fb_response}")
    else:
        print("⚠ Facebook publishing not configured")
    
    print("\n=== Publishing Complete ===")

if __name__ == "__main__":
    # Update this path to your video
    video_path = "output/20261106_205647_755588_short.mp4"
    
    # Optional: Load script data from JSON if available
    script_data = None
    script_file = video_path.replace('.mp4', '_script.json')
    if os.path.exists(script_file):
        with open(script_file, 'r', encoding='utf-8') as f:
            script_data = json.load(f)
        print(f"Loaded script data from {script_file}")
    
    publish_existing_video(video_path, script_data)
