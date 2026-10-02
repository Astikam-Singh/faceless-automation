import json
with open('scripts/pregenerated/longform_only.json', 'r') as f:
    data = json.load(f)
    print(f"Keys: {list(data.keys())}")
    print(f"Longform count: {len(data.get('longform', []))}")
    print(f"Shortform count: {len(data.get('shortform', []))}")
