import os
import yaml
from google import genai
from google.genai import types

class ScriptGenerator:
    def __init__(self, config_path=None):
        if config_path is None:
            # Resolve path relative to this file's location (src/), looking for config.yaml in parent dir (./)
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.yaml')
            
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.load(f, Loader=yaml.SafeLoader)
        
        # Load API key from env or config
        api_key = os.getenv("GOOGLE_GEMINI_API_KEY", self.config.get("google_gemini_api_key", ""))
        self.client = genai.Client(api_key=api_key) if api_key and api_key != "YOUR_GEMINI_API_KEY" else genai.Client()

    def generate_script(self, is_longform=False):
        brand = self.config['niche'].get('brand_name', 'Ancient Mindset Lab')
        min_dur = self.config['niche'].get('min_longform_minutes', 10) if is_longform else (self.config['niche'].get('min_shortform_seconds', 30)/60)
        max_dur = self.config['niche'].get('max_longform_minutes', 25) if is_longform else (self.config['niche'].get('max_shortform_seconds', 60)/60)
        
        duration_desc = f"{min_dur}-{max_dur} minutes" if is_longform else f"{int(min_dur*60)}-{int(max_dur*60)} seconds"
        type_desc = "long-form YouTube video" if is_longform else "short-form Instagram Reel/YouTube Short"
        
        prompt = (
            f"You are an expert viral scriptwriter for '{brand}' in the '{self.config['niche']['name']}' niche targeting USA audiences. "
            f"Write a high-retention {type_desc} script (duration: {duration_desc}). "
            f"The brand voice is '{brand}' - authoritative, scientific yet ancient, and deeply philosophical. "
            "Requirements:\n"
            "1. Hook the viewer in the first 3-5 seconds with a powerful, counter-intuitive statement.\n"
            "2. Keep pacing tight and punchy.\n"
            "3. Include bracketed visual keywords [e.g., [cinematic dark aesthetic, rain on window]] at the start of each segment.\n"
            f"4. End with a subtle call to action: 'Join the {brand} for more ancient wisdom.'\n"
            "5. If generating a long-form script, ensure it is extremely detailed, with at least 50 distinct segments to ensure a 10-12 minute runtime (approximately 150 words per minute).\n"
            "6. Return valid JSON with keys: 'title', 'description', 'hashtags', and 'segments' (list of {'text', 'visual_prompt'})."
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
