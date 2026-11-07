"""
Quick script to verify Facebook Page ID and get valid page IDs.
"""

import requests
import yaml

# Load config
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

fb_config = config['publishing']['facebook']
access_token = fb_config['access_token']
page_id = fb_config['page_id']

print("Facebook Page ID Verification")
print("=" * 50)

# Test 1: Validate access token
print("\n1. Testing Access Token...")
url = f"https://graph.facebook.com/v25.0/me?access_token={access_token}"
response = requests.get(url)
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ Token is valid")
    print(f"   User ID: {data.get('id')}")
    print(f"   Name: {data.get('name', 'N/A')}")
else:
    print(f"   ❌ Token is invalid: {response.status_code}")
    print(f"   {response.text}")
    exit()

# Test 2: Get all pages accessible with this token
print("\n2. Fetching Available Pages...")
url = f"https://graph.facebook.com/v25.0/me/accounts?access_token={access_token}"
response = requests.get(url)
if response.status_code == 200:
    data = response.json()
    if 'data' not in data or not data['data']:
        print("   ❌ No pages found. Make sure you have admin access to a Facebook Page.")
    else:
        print("   ✅ Available Pages:")
        for i, page in enumerate(data['data'], 1):
            print(f"\n   Page {i}:")
            print(f"      ID: {page['id']}")
            print(f"      Name: {page['name']}")
            print(f"      Username: {page.get('username', 'N/A')}")
            print(f"      Category: {page.get('category', 'N/A')}")
            
            # Test if this page can upload videos
            page_access_token = page.get('access_token')
            if page_access_token:
                test_url = f"https://graph.facebook.com/v25.0/{page['id']}/videos?access_token={page_access_token}"
                test_response = requests.get(test_url)
                print(f"      Video Upload: {'✅ Possible' if test_response.status_code == 400 else '⚠ Check needed'} (400 = OK, means endpoint exists)")
else:
    print(f"   ❌ Failed to fetch pages: {response.status_code}")

print("\n" + "=" * 50)
print(f"\nCurrent config page_id: {page_id}")
print("If the ID above doesn't match, update config.yaml")
