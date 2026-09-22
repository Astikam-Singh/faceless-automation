import asyncio
import edge_tts
import yaml
import os

class TextToSpeech:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.load(f, Loader=yaml.SafeLoader)
        self.voice = self.config.get("tts", {}).get("voice", "en-US-ChristopherNeural")

    async def _generate(self, segments: list, output_path: str):
        # Build text without problematic SSML tags that might be read aloud
        text = " ".join([seg['text'].replace('&', 'and') for seg in segments])
        
        # Use plain text for more reliable synthesis if tags fail
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(output_path)

    def generate_voiceover(self, segments: list, output_path: str = "output/voiceover.mp3"):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        asyncio.run(self._generate(segments, output_path))
        return output_path

if __name__ == "__main__":
    tts = TextToSpeech()
    path = tts.generate_voiceover(["Control your mind, for outside forces have no power over your inner citadel."])
    print(f"Voiceover saved to {path}")
