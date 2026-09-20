import os
import yaml
from google import genai
from google.genai import types

class ScriptGenerator:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.load(f, Loader=yaml.SafeLoader)
        
        # Load API key from env or config
        api_key = os.getenv("GOOGLE_GEMINI_API_KEY", self.config.get("google_gemini_api_key", ""))
        self.client = genai.Client(api_key=api_key) if api_key and api_key != "YOUR_GEMINI_API_KEY" else genai.Client()

    def generate_script(self):
        brand = self.config['niche'].get('brand_name', 'Ancient Mindset Lab')
        prompt = (
            f"You are an expert viral scriptwriter for '{brand}' in the '{self.config['niche']['name']}' niche targeting USA audiences. "
            f"Write a high-retention vertical video script (maximum {self.config['niche']['video_duration_seconds']} seconds when spoken). "
            f"The brand voice is '{brand}' - authoritative, scientific yet ancient, and deeply philosophical. "
            "Requirements:\n"
            "1. Hook the viewer in the first 3 seconds with a powerful statement.\n"
            "2. Keep pacing tight and punchy.\n"
            "3. Include suggested visual keywords in brackets [e.g., [cinematic dark aesthetic]].\n"
            f"4. End with a subtle call to action: 'Join the {brand} for more ancient wisdom.'\n"
            "5. Return valid JSON with keys: 'title', 'description', 'hashtags', and 'segments' (list of {'text', 'visual_prompt'})."
        )

        response = self.client.models.generate_content(
            model='gemini-3.1-flash-lite',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.7,
            ),
        )
        
        import json
        return json.loads(response.text)

if __name__ == "__main__":
    gen = ScriptGenerator()
    script = gen.generate_script()
    print(json.dumps(script, indent=2))
