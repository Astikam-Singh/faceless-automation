import os
import cv2
import numpy as np
import whisper

class QAEngine:
    """
    Quality Assurance engine for video and audio content.
    """
    def __init__(self):
        # Load whisper for audio transcript verification
        self.model = whisper.load_model("base")

    def analyze_audio(self, audio_path, expected_text):
        """Analyze audio to ensure it's not robotic and matches text."""
        result = self.model.transcribe(audio_path)
        transcript = result["text"].lower()
        
        # Simple heuristic: If it contains tags, it failed the TTS synthesis
        leak_keywords = ["prosody", "speak", "version", "xml"]
        for keyword in leak_keywords:
            if keyword in transcript:
                print(f"âŒ Audio QA Failed: Detected TTS tag leakage ('{keyword}')")
                return 0.2  # Low score

        # Check for transcription similarity (simple length check)
        if len(transcript) < len(expected_text) * 0.5:
             print("âŒ Audio QA Failed: Transcription too short.")
             return 0.4
        
        return 1.0 # Successful

    def analyze_video(self, video_path):
        """Analyze video frames for stuck or black screen issues."""
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        black_frames = 0
        stuck_frames = 0
        last_frame = None

        for _ in range(0, total_frames, 30): # Sample every 30 frames
            ret, frame = cap.read()
            if not ret: break
            
            mean_intensity = np.mean(frame)
            if mean_intensity < 5: black_frames += 1
            
            if last_frame is not None and np.array_equal(frame, last_frame):
                stuck_frames += 1
            last_frame = frame
        
        cap.release()
        
        success_rate = 1.0 - ((black_frames + stuck_frames) / (total_frames / 30))
        if success_rate < 0.8:
            print(f"âŒ Video QA Failed: Success rate {success_rate:.2f} too low.")
        return success_rate

    def run_qa(self, video_path, audio_path, expected_text):
        video_score = self.analyze_video(video_path)
        audio_score = self.analyze_audio(audio_path, expected_text)
        
        total_score = (video_score + audio_score) / 2
        print(f"\nðŸ“Š QA Report:")
        print(f"   - Video Score: {video_score*100:.1f}%")
        print(f"   - Audio Score: {audio_score*100:.1f}%")
        print(f"   - Final Success Rate: {total_score*100:.1f}%")
        
        return total_score
