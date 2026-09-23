import os
from src.script_generator import ScriptGenerator
from src.renderer import VideoRenderer
from src.tts import TextToSpeech
from src.assets import AssetFetcher
from src.thumbnail import ThumbnailGenerator
from src.video_formatter import VideoFormatter

def test_config_loading():
    print(f"Testing config loading from: {os.getcwd()}")
    try:
        ScriptGenerator()
        print("ScriptGenerator: Success")
        VideoRenderer(is_longform=True)
        print("VideoRenderer: Success")
        TextToSpeech()
        print("TextToSpeech: Success")
        AssetFetcher()
        print("AssetFetcher: Success")
        ThumbnailGenerator()
        print("ThumbnailGenerator: Success")
        VideoFormatter(is_longform=True)
        print("VideoFormatter: Success")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_config_loading()