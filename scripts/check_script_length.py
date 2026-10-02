import json

try:
    with open('scripts/pregenerated/longform_only.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print(f"Validation Successful.")
    print(f"Longform scripts found: {len(data['longform'])}")
    for i, script in enumerate(data['longform']):
        segment_count = len(script.get('segments', []))
        print(f"Script {i+1}: {segment_count} segments")
        
        # Estimate duration (very rough estimate: 1 segment = 10-15 seconds)
        # 60 segments * 12 seconds = 720 seconds = 12 minutes.
        estimated_minutes = (segment_count * 12) / 60
        print(f"   Estimated duration: approx {estimated_minutes:.1f} minutes")
        
except Exception as e:
    print(f"Validation Failed: {e}")
