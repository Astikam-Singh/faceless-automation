import os
import time
import yaml
import requests
from datetime import datetime

class FacebookPublisher:
    """
    Handles publishing short-form videos to Facebook Reels / Page Videos
    using Meta Graph API.
    """
    API_BASE = "https://graph.facebook.com/v25.0"

    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.load(f, Loader=yaml.SafeLoader)

        fb_config = self.config.get('publishing', {}).get('facebook', {})
        self.enabled = fb_config.get('enabled', False)
        self.access_token = fb_config.get('access_token', '')
        self.page_id = fb_config.get('page_id', '')

    def is_ready(self):
        return bool(self.enabled and self.access_token and self.page_id and self.access_token != "YOUR_FB_ACCESS_TOKEN")

    def upload_reel(self, script_data, video_path):
        """
        Uploads video to Facebook Page / Reel via Graph API.
        """
        if not self.enabled:
            print("Facebook publishing disabled in config")
            return None

        if not os.path.exists(video_path):
            print(f"❌ Video file not found: {video_path}")
            return None

        if not self.is_ready():
            print("⚠ Facebook not configured: add access_token and page_id to config.yaml")
            return None

        title = script_data.get('title', 'Stoic Wisdom')
        description = f"{title}\n\n#Stoicism #Mindset #Reels #Philosophy #SelfImprovement"

        print(f"\n[Facebook Reels Upload] Preparing to upload: {title}")
        file_size = os.path.getsize(video_path) / (1024 * 1024)
        print(f"📊 Video size: {file_size:.2f} MB")

        url = f"{self.API_BASE}/{self.page_id}/videos"
        
        try:
            with open(video_path, 'rb') as video_file:
                files = {'source': video_file}
                data = {
                    'access_token': self.access_token,
                    'description': description,
                    'published': 'true'
                }
                response = requests.post(url, data=data, files=files, timeout=120)
                response.raise_for_status()
                result = response.json()
                video_id = result.get('id')
                print(f"✅ Facebook upload successful! Video ID: {video_id}")
                return result
        except Exception as e:
            print(f"❌ Facebook Upload Failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            return None

if __name__ == "__main__":
    pub = FacebookPublisher()
    print(f"Facebook Publisher ready: {pub.is_ready()}")
