from src.publishers.youtube import YouTubePublisher
import json
import os

# Load the script data
with open("scripts/pregenerated/batch_1.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Assuming we use the first script as the candidate for now, or match by title
# This approach uses the first longform script
script = data["longform"][0]
video_path = "output/20261007_231942_707531_long.mp4"
# Using a likely thumbnail path derived from the run_id, check existence
thumb_candidate = "output/20261007_231942_707531_thumb.jpg"
thumbnail_path = thumb_candidate if os.path.exists(thumb_candidate) else None

if not os.path.exists(video_path):
    print(f"❌ Video file not found: {video_path}")
    exit(1)

print(f"🚀 Publishing: {script['title']}")
pub = YouTubePublisher()
pub.upload_video(script, video_path, thumbnail_path=thumbnail_path)
print("✅ Auto-publishing request submitted.")
