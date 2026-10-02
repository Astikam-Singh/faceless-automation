import cv2
import os

def check_video(video_path):
    if not os.path.exists(video_path):
        return f"File not found: {video_path}"
    
    cap = cv2.VideoCapture(video_path)
    
    # Get metadata
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    
    # Calculate duration
    duration_seconds = frame_count / fps if fps > 0 else 0
    
    cap.release()
    
    return {
        "path": video_path,
        "resolution": f"{int(width)}x{int(height)}",
        "fps": round(fps, 2),
        "duration_minutes": round(duration_seconds / 60, 2),
        "duration_seconds": round(duration_seconds, 2)
    }

files = ["output/20261002_144541_0_shortform.mp4", "output/20261002_144541_0_longform.mp4"]
for f in files:
    print(check_video(f))
