from src.publishers.youtube import YouTubePublisher
import json
import os

video_path = "output/20261010_152007_980308_long.mp4"

if not os.path.exists(video_path):
    print(f"❌ Video file not found: {video_path}")
    exit(1)

# Load the script data from the batch file
try:
    with open("scripts/pregenerated/longform_only.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    # Using the first longform script as the metadata source
    script = data["longform"][0]
except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
    print(f"⚠️ Could not load script metadata, using default: {e}")
    script = {
        "title": "Ancient Wisdom Deep Dive",
        "description": "Exploration of Stoic principles.",
        "hashtags": "#stoic #philosophy"
    }

print(f"🚀 Publishing Longform: {script['title']}")
try:
    pub = YouTubePublisher()
    pub.upload_video(script, video_path)
    print("✅ Auto-publishing request submitted.")
except Exception as e:
    print(f"❌ Publication failed: {e}")
    print("💡 If this was an AuthenticationError, run scripts/force_auth.py locally.")
