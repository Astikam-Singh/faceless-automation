"""
Facebook/Instagram Token Helper Script
Generates and refreshes access tokens for Facebook Graph API and Instagram Graph API.
"""

import os
import sys
import yaml
import requests
import time
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler to capture OAuth callback."""
    def __init__(self, *args, **kwargs):
        self.authorization_code = None
        self.auth_state = None
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle OAuth callback."""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if 'code' in params:
            self.authorization_code = params['code'][0]
            self.auth_state = params.get('state', [None])[0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h1>Authorization Successful!</h1><p>You can close this window.</p></body></html>')
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'<html><body><h1>Authorization Failed</h1></body></html>')


def load_config(config_path="config.yaml"):
    """Load configuration from YAML file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def save_config(config, config_path="config.yaml"):
    """Save configuration to YAML file."""
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


def get_app_credentials(config):
    """Get Facebook app credentials from config or environment."""
    # Check config first
    fb_config = config.get('facebook', {})
    app_id = fb_config.get('app_id') or os.environ.get('FACEBOOK_APP_ID')
    app_secret = fb_config.get('app_secret') or os.environ.get('FACEBOOK_APP_SECRET')
    
    if not app_id or not app_secret:
        print("❌ Facebook App ID and App Secret required")
        print("   Add to config.yaml or set FACEBOOK_APP_ID and FACEBOOK_APP_SECRET env vars")
        return None, None
    
    return app_id, app_secret


def get_user_access_token(app_id, app_secret):
    """
    Get a short-lived user access token via OAuth flow.
    Opens browser for user to authenticate.
    """
    # Generate a random state for CSRF protection
    state = f"fb_{int(time.time())}"
    
    # OAuth endpoints
    auth_url = "https://www.facebook.com/v25.0/dialog/oauth"
    token_url = "https://graph.facebook.com/v25.0/oauth/access_token"
    
    # Required permissions
    permissions = [
        "pages_show_list",
        "pages_read_engagement", 
        "pages_manage_posts",
        "instagram_basic",
        "instagram_content_publish"
    ]
    
    redirect_uri = "http://localhost:8000/callback"
    
    # Build authorization URL
    auth_params = {
        'client_id': app_id,
        'redirect_uri': redirect_uri,
        'state': state,
        'scope': ','.join(permissions)
    }
    
    auth_request_url = f"{auth_url}?{'&'.join(f'{k}={v}' for k, v in auth_params.items())}"
    
    print(f"\n🌐 Opening browser for Facebook authentication...")
    print(f"   URL: {auth_request_url}")
    print("   If browser doesn't open, copy the URL to your browser.")
    
    # Open browser
    webbrowser.open(auth_request_url)
    
    # Start local server to capture callback
    server = HTTPServer(('localhost', 8000), OAuthCallbackHandler)
    server.timeout = 300  # 5 minute timeout
    
    print("\n⏳ Waiting for authentication... (timeout in 5 minutes)")
    print("   Press Ctrl+C to cancel")
    
    try:
        server.handle_request()
        
        if server.authorization_code:
            # Exchange code for token
            token_params = {
                'client_id': app_id,
                'client_secret': app_secret,
                'redirect_uri': redirect_uri,
                'code': server.authorization_code
            }
            
            print("\n🔄 Exchanging authorization code for access token...")
            response = requests.get(token_url, params=token_params)
            response.raise_for_status()
            
            token_data = response.json()
            access_token = token_data.get('access_token')
            
            if access_token:
                print(f"✅ User access token obtained!")
                return access_token, state
            else:
                print(f"❌ Failed to get access token: {token_data}")
                return None, None
        else:
            print("\n❌ Authorization failed or cancelled")
            return None, None
            
    except KeyboardInterrupt:
        print("\n\n❌ Authorization cancelled by user")
        return None, None
    finally:
        server.server_close()


def get_long_lived_token(user_token, app_id, app_secret):
    """Exchange short-lived token for long-lived token (60 days)."""
    token_url = "https://graph.facebook.com/v25.0/oauth/access_token"
    
    params = {
        'grant_type': 'fb_exchange_token',
        'client_id': app_id,
        'client_secret': app_secret,
        'fb_exchange_token': user_token
    }
    
    print("\n🔄 Exchanging for long-lived token (60 days)...")
    response = requests.get(token_url, params=params)
    response.raise_for_status()
    
    data = response.json()
    long_lived_token = data.get('access_token')
    expires_in = data.get('expires_in', 0)
    
    if long_lived_token:
        print(f"✅ Long-lived token obtained! Expires in {expires_in // 86400} days")
        return long_lived_token
    else:
        print(f"❌ Failed to get long-lived token: {data}")
        return None


def get_page_access_token(user_token, app_id, app_secret):
    """Get page access token from user token."""
    url = "https://graph.facebook.com/v25.0/me/accounts"
    
    params = {
        'access_token': user_token
    }
    
    print("\n📊 Fetching Facebook Pages...")
    response = requests.get(url, params=params)
    response.raise_for_status()
    
    data = response.json()
    
    if 'data' not in data or not data['data']:
        print("❌ No Facebook Pages found. Make sure you have admin access to a Facebook Page.")
        return None, None
    
    print("\n📁 Available Pages:")
    for i, page in enumerate(data['data'], 1):
        print(f"   {i}. {page['name']} (ID: {page['id']})")
    
    # Auto-select first page or let user choose
    if len(data['data']) == 1:
        selected_page = data['data'][0]
        print(f"\n✅ Selected: {selected_page['name']}")
    else:
        choice = input("\nSelect page number (default 1): ").strip() or "1"
        try:
            selected_page = data['data'][int(choice) - 1]
        except (ValueError, IndexError):
            selected_page = data['data'][0]
            print(f"Invalid choice. Using first page: {selected_page['name']}")
    
    page_access_token = selected_page.get('access_token')
    page_id = selected_page.get('id')
    
    return page_access_token, page_id


def get_instagram_account_id(page_access_token):
    """Get Instagram Business Account ID linked to Facebook Page."""
    url = "https://graph.facebook.com/v25.0/me/accounts"
    
    params = {
        'access_token': page_access_token,
        'fields': 'instagram_business_accounts{id,username}'
    }
    
    print("\n📸 Fetching Instagram Business Accounts...")
    response = requests.get(url, params=params)
    response.raise_for_status()
    
    data = response.json()
    
    if 'data' not in data or not data['data']:
        print("❌ No Instagram Business Accounts found.")
        print("   Link your Instagram account to your Facebook Page first.")
        return None
    
    instagram_account = data['data'][0]
    instagram_id = instagram_account.get('id')
    username = instagram_account.get('username', 'unknown')
    
    print(f"✅ Found Instagram account: @{username} (ID: {instagram_id})")
    return instagram_id


def save_tokens_to_config(config, page_access_token, page_id, instagram_id=None, instagram_token=None):
    """Save tokens to config.yaml."""
    if 'publishing' not in config:
        config['publishing'] = {}
    
    # Save Facebook tokens
    config['publishing']['facebook'] = {
        'enabled': True,
        'access_token': page_access_token,
        'page_id': page_id
    }
    
    # Save Instagram tokens if provided
    if instagram_token and instagram_id:
        config['publishing']['instagram'] = {
            'enabled': True,
            'access_token': instagram_token,
            'instagram_account_id': instagram_id
        }
    
    save_config(config)
    print("\n💾 Tokens saved to config.yaml")


def main():
    """Main token generation flow."""
    print("=" * 60)
    print("Facebook/Instagram Token Generator")
    print("=" * 60)
    
    # Load config
    config = load_config()
    
    # Get app credentials
    print("\n🔑 Step 1: Get App Credentials")
    app_id, app_secret = get_app_credentials(config.get('facebook', {}))
    
    if not app_id or not app_secret:
        print("\n📝 Instructions:")
        print("   1. Go to https://developers.facebook.com/apps/")
        print("   2. Create a new app (or use existing)")
        print("   3. Add 'Facebook Login' product")
        print("   4. Copy App ID and App Secret")
        print("   5. Add them to config.yaml under 'facebook' section:")
        print("      facebook:")
        print("        app_id: YOUR_APP_ID")
        print("        app_secret: YOUR_APP_SECRET")
        return
    
    print(f"   App ID: {app_id}")
    
    # Get user access token
    print("\n👤 Step 2: User Authentication")
    user_token, state = get_user_access_token(app_id, app_secret)
    
    if not user_token:
        return
    
    # Get long-lived token
    long_lived_token = get_long_lived_token(user_token, app_id, app_secret)
    
    # Get page access token
    print("\n🏢 Step 3: Get Page Access Token")
    page_access_token, page_id = get_page_access_token(long_lived_token, app_id, app_secret)
    
    if not page_access_token:
        return
    
    # Get Instagram account
    print("\n📸 Step 4: Get Instagram Account")
    instagram_id = get_instagram_account_id(page_access_token)
    
    if instagram_id:
        # For Instagram, we can use the same page access token
        # or get a separate Instagram token
        print("\n🔄 Using Page Access Token for Instagram (simplified)")
        instagram_token = page_access_token
    else:
        instagram_token = None
    
    # Save to config
    save_tokens_to_config(config, page_access_token, page_id, instagram_id, instagram_token)
    
    print("\n" + "=" * 60)
    print("✅ Token generation complete!")
    print("=" * 60)
    print("\nYou can now test publishing with:")
    print("   python publish_existing_video.py")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
