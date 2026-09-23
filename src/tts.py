import os
import yaml
import subprocess
import sys

class TextToSpeech:
    """
    Handles voiceover generation using LOCAL Piper TTS model for offline reliability.
    """
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r", encoding='utf-8') as f:
            self.config = yaml.load(f, Loader=yaml.SafeLoader)
        
        # Path to the model file you need to download
        self.model_path = "assets/en_US-lessac-medium.onnx"

    def generate_voiceover(self, segments: list, output_path: str = "output/voiceover.mp3"):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Combine text segments
        text = " ".join([seg['text'].replace('&', 'and') for seg in segments])
        
        print(f"🔊 Generating local voiceover with Piper: {text[:50]}...")
        
        # Piper expects text via stdin
        cmd = [sys.executable, "-m", "piper", "--model", self.model_path, "--output_file", output_path]
        
        try:
            # Need to ensure 'piper' is in system PATH
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate(input=text.encode('utf-8'))
            
            if process.returncode == 0:
                print(f"✅ Local Voiceover saved to {output_path}")
                return output_path
            else:
                error_msg = stderr.decode('utf-8')
                print(f"❌ Piper TTS Error: {error_msg}")
                return None
        except FileNotFoundError:
            print("❌ 'piper' executable not found. Please install Piper TTS via 'pip install piper-tts'")
            return None
        except Exception as e:
            print(f"❌ TTS Failed: {e}")
            return None
