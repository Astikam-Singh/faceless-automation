import os
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube'
]

print("--- Starting YouTube Authentication Flow (Isolated) ---")

if not os.path.exists("client_secret.json"):
    print("❌ Error: 'client_secret.json' not found.")
else:
    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secret.json", 
        SCOPES
    )
    creds = flow.run_local_server(port=0)
    
    with open("token.pickle", 'wb') as f:
        pickle.dump(creds, f)
    print("✅ Successfully authenticated. 'token.pickle' has been created.")
