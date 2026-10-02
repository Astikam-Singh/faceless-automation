from src.publishers.youtube import YouTubePublisher
import os

print("--- Starting YouTube Authentication Flow ---")
print("This will open a browser window to authenticate with your YouTube account.")
print("Once authenticated, 'token.pickle' will be created in the root directory.")

if not os.path.exists("client_secret.json"):
    print("❌ Error: 'client_secret.json' not found in workspace root.")
    print("Please ensure your Google Cloud credentials are placed there.")
else:
    # This will trigger the _authenticate() method in the constructor
    pub = YouTubePublisher()
    print("✅ Successfully authenticated. 'token.pickle' has been refreshed/created.")
