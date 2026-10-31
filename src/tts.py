import os
from kokoro_onnx import Kokoro
import soundfile as sf

class TextToSpeech:
    """
    Handles voiceover generation using Kokoro ONNX for high-quality TTS.
    """
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.kokoro = Kokoro(
            os.path.join(base_dir, "assets", "kokoro-v1.0.onnx"),
            os.path.join(base_dir, "assets", "voices-v1.0.bin")
        )

    def generate_voiceover(self, segments: list, output_path: str = "output/voiceover.wav"):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        text = " ".join([seg["text"].replace("&", "and") for seg in segments])
        text = text.strip()
        
        if not text:
            return None
        
        print(f"🔊 Generating local voiceover with Kokoro: {text[:50]}...")
        
        try:
            samples, sample_rate = self.kokoro.create(
                text,
                voice="af_heart",
                speed=1.0,
                lang="en-us",
            )
            sf.write(output_path, samples, sample_rate)
            print(f"✅ Local Voiceover saved to {output_path}")
            return output_path
        except Exception as e:
            print(f"❌ TTS Failed: {e}")
            return None
