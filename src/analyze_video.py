import cv2
import numpy as np

def analyze_video(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error opening video file: {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"FPS: {fps}, Total Frames: {total_frames}")

    # Check frames at specific intervals
    check_times = [0, 5, 10, 20] # in seconds
    last_frame = None
    
    for t in check_times:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ret, frame = cap.read()
        if not ret:
            print(f"Could not read frame at {t}s")
            continue
            
        mean_intensity = np.mean(frame)
        print(f"Frame at {t}s: Mean Intensity = {mean_intensity:.2f}")
        
        # Check if frame is mostly black (mean intensity < 10)
        if mean_intensity < 10:
            print(f"  ⚠ Frame at {t}s is mostly black!")
            
        # Check if identical to previous
        if last_frame is not None and np.array_equal(frame, last_frame):
            print(f"  ⚠ Frame at {t}s is identical to {check_times[check_times.index(t)-1]}s! (Stuck frame)")
            
        last_frame = frame
        
    cap.release()

if __name__ == "__main__":
    analyze_video("output/final_video.mp4")
