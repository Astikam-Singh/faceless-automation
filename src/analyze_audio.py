import os
from moviepy.editor import AudioFileClip

def analyze_audio(audio_path):
    if not os.path.exists(audio_path):
        print(f"File not found: {audio_path}")
        return
        
    audio = AudioFileClip(audio_path)
    print(f"Audio File: {audio_path}")
    print(f"Duration: {audio.duration:.2f}s")
    print(f"Sample Rate: {audio.fps}Hz")
    
    # Check for long silences
    # In a real scenario, this would involve processing amplitude
    # For a quick initial check, we just look at the duration vs what was expected.
    
    audio.close()

if __name__ == "__main__":
    analyze_audio("output/voiceover.mp3")