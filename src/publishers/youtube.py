import os
import json
import yaml
import time
import pickle
from datetime import datetime
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class YouTubePublisher:
    """
    Handles publishing to YouTube with OAuth2 authentication.
    Creates token.pickle automatically on first run.
    """
    
    SCOPES = [
        'https://www.googleapis.com/auth/youtube.upload',
        'https://www.googleapis.com/auth/youtube'
    ]
    
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.load(f, Loader=yaml.SafeLoader)
        
        self.brand_name = self.config['niche']['brand_name']
        self.channel_id = self.config['publishing']['youtube']['channel_id']
        self.client_secret_file = self.config['publishing']['youtube'].get('client_secret_file', 'client_secret.json')
        self.youtube = self._authenticate()
    
    def _authenticate(self):
        """
        Authenticate with YouTube API using OAuth2.
        Creates token.pickle automatically on first run.
        """
        creds = None
        token_file = 'token.pickle'
        
        # Check if token.pickle exists (from previous auth)
        if os.path.exists(token_file):
            print("✅ Found saved credentials (token.pickle)")
            with open(token_file, 'rb') as f:
                creds = pickle.load(f)
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("🔄 Refreshing expired credentials...")
                creds.refresh(Request())
            else:
                print(f"🌐 No valid credentials found. Starting OAuth flow...")
                print(f"   Looking for client_secret.json at: {self.client_secret_file}")
                
                if not os.path.exists(self.client_secret_file):
                    print(f"❌ ERROR: {self.client_secret_file} not found!")
                    print("   Please download it from Google Cloud Console")
                    return None
                
                print("   Opening browser for authentication...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secret_file, 
                    self.SCOPES
                )
                creds = flow.run_local_server(port=0)
                
                # Save credentials for future runs
                with open(token_file, 'wb') as f:
                    pickle.dump(creds, f)
                print(f"✅ Credentials saved to {token_file}")
        
        # Build YouTube API client
        youtube = build('youtube', 'v3', credentials=creds)
        print("✅ YouTube API client initialized")
        return youtube
        
    def generate_youtube_metadata(self, script_data, video_path):
        """Generate YouTube video metadata with SEO optimization."""
        title = script_data.get('title', 'Ancient Wisdom')
        
        # Add brand prefix to title
        if not title.lower().startswith(self.brand_name.lower()):
            title = f"{self.brand_name} | {title}"
        
        # Generate description
        description = f"""
{script_data.get('description', '')}

Join {self.brand_name} for daily stoic wisdom and modern mindset strategies.
👉 Subscribe for more: https://youtube.com/channel/{self.channel_id}

#Stoicism #Mindset #SelfImprovement #AncientWisdom #PersonalGrowth
"""
        
        # Generate hashtags
        hashtags = script_data.get('hashtags', [])
        if isinstance(hashtags, list):
            hashtags_str = " ".join(h for h in hashtags if h.startswith('#'))
        else:
            hashtags_str = "#Stoicism #Mindset #AncientWisdom"
        
        # Set tags for YouTube algorithm
        tags = [
            self.brand_name,
            "stoicism",
            "mindset",
            "self-improvement",
            "ancient wisdom",
            "philosophy",
            "personal growth",
            "mental strength",
            "emotional resilience",
            "Marcus Aurelius",
            "epictetus",
            "seneca"
        ]
        
        # Add niche-specific tags
        niche_tags = self.config['niche']['name'].lower().replace('&', '').split()
        tags.extend(niche_tags)
        
        return {
            'file': video_path,
            'title': title,
            'description': description,
            'tags': tags,
            'category': '22',  # Education category
            'privacy': 'public',
            'thumbnail': None  # Will be set if thumbnail is provided
        }
    
    def upload_video(self, script_data, video_path, thumbnail_path=None, max_retries=3):
        """
        Upload video to YouTube with retry logic and thumbnail support.
        Returns upload status and video URL if successful.
        """
        if not self.config['publishing']['youtube']['enabled']:
            print("YouTube publishing disabled in config")
            return None
        
        # Generate metadata
        metadata = self.generate_youtube_metadata(script_data, video_path)
        
        print(f"\n[YouTube Upload] Preparing to upload: {metadata['title']}")
        
        # Check if video file exists
        if not os.path.exists(video_path):
            print(f"❌ Video file not found: {video_path}")
            return None
        
        file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
        print(f"📊 Video size: {file_size:.2f} MB")
        
        # Check if authenticated
        if not self.youtube:
            print("❌ YouTube API not authenticated. Run authentication first.")
            return None
        
        print(f"🚀 Uploading to YouTube...")
        print(f"   - Title: {metadata['title']}")
        print(f"   - Category: Education")
        print(f"   - Privacy: {metadata['privacy']}")
        
        try:
            # Prepare video upload
            body = {
                'snippet': {
                    'title': metadata['title'],
                    'description': metadata['description'],
                    'tags': metadata['tags'],
                    'categoryId': metadata['category']
                },
                'status': {
                    'privacyStatus': metadata['privacy'],
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # Create media upload object
            media = MediaFileUpload(
                video_path,
                mimetype='video/mp4',
                resumable=True
            )
            
            # Execute upload
            request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = request.execute()
            
            video_id = response['id']
            video_url = f"https://youtu.be/{video_id}"
            
            print(f"\n✅ YouTube upload successful!")
            print(f"   Video ID: {video_id}")
            print(f"   Video URL: {video_url}")

            # Upload custom thumbnail if provided
            if thumbnail_path and os.path.exists(thumbnail_path):
                self.set_video_thumbnail(video_id, thumbnail_path)
            
            return {
                'success': True,
                'video_id': video_id,
                'video_url': video_url,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Upload failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def set_video_thumbnail(self, video_id, thumbnail_path):
        """Set custom thumbnail for uploaded video via YouTube API."""
        if not thumbnail_path or not os.path.exists(thumbnail_path):
            print(f"Thumbnail not found: {thumbnail_path}")
            return False
        
        try:
            print(f"🖼 Uploading custom thumbnail: {thumbnail_path}")
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path, mimetype='image/jpeg')
            ).execute()
            print(f"✅ Thumbnail set for video {video_id}")
            return True
        except Exception as e:
            print(f"⚠️ Could not set thumbnail: {e}")
            return False

if __name__ == "__main__":
    publisher = YouTubePublisher()
    print("YouTube Publisher initialized")
