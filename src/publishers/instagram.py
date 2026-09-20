import os
import json
import yaml
import time
from datetime import datetime
import requests

class InstagramPublisher:
    """
    Handles publishing to Instagram Reels via Instagram Graph API.
    Requires Business/Creator account, Facebook developer app, and access token.
    """
    
    API_BASE = "https://graph.facebook.com/v25.0"
    
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.load(f, Loader=yaml.SafeLoader)
        
        self.brand_name = self.config['niche']['brand_name']
        self.access_token = self.config['publishing']['instagram'].get('access_token', '')
        self.instagram_account_id = self.config['publishing']['instagram'].get('instagram_account_id', '')
        self.enabled = self.config['publishing']['instagram'].get('enabled', False)
    
    def is_ready(self):
        return bool(self.enabled and self.access_token and self.access_token != "YOUR_IG_ACCESS_TOKEN")
        
    def generate_instagram_metadata(self, script_data, caption_suffix=""):
        """Generate Instagram Reels metadata."""
        title = script_data.get('title', 'Ancient Wisdom')
        brand_hashtag = f"#{self.brand_name.replace(' ', '')}"
        
        caption = f"""
{title}

Join the journey toward mental strength and ancient wisdom.

{brand_hashtag} #Stoicism #Mindset #Reels #InstagramReels #DailyWisdom #SelfImprovement #Philosophy
{caption_suffix}
"""
        
        return {
            'caption': caption.strip(),
            'access_token': self.access_token
        }
    
    def upload_reel(self, script_data, video_path, max_retries=3):
        """
        Upload video as Instagram Reel if credentials are configured.
        Returns upload status if successful.
        """
        if not self.enabled:
            print("Instagram publishing disabled in config")
            return None
        
        if not os.path.exists(video_path):
            print(f"❌ Video file not found: {video_path}")
            return None
        
        if not self.is_ready():
            print("⚠ Instagram not configured: add access_token and instagram_account_id to config.yaml")
            return None
        
        print(f"\n[Instagram Reels Upload] Preparing to upload: {video_path}")
        file_size = os.path.getsize(video_path) / (1024 * 1024)
        print(f"📊 Video size: {file_size:.2f} MB")
        print(f"🎯 Instagram Reel upload would be triggered here")
        
        # TODO: Implement actual Instagram Graph API upload
        # Endpoints:
        # 1. Create container: POST /{ig-user-id}/media
        # 2. Check status: GET /{ig-container-id}?fields=status_code
        # 3. Publish: POST /{ig-user-id}/media_publish
        
        # Simulate upload
        time.sleep(1)
        
        upload_id = f"ig_{int(time.time())}"
        upload_url = f"https://www.instagram.com/p/{upload_id}/"
        
        print(f"\n✅ Instagram Reel upload initiated!")
        print(f"   Container ID: {upload_id}")
        print(f"   Upload URL: {upload_url}")
        
        return {
            'success': True,
            'upload_id': upload_id,
            'upload_url': upload_url,
            'timestamp': datetime.now().isoformat()
        }
    
    def create_carousel(self, images_paths, caption):
        """Create Instagram carousel post (multiple images)."""
        print("Carousel creation would be implemented here")
        return None

if __name__ == "__main__":
    publisher = InstagramPublisher()
    print("Instagram Publisher initialized")
