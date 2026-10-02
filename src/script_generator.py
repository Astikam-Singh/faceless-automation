import os
import yaml
import json
import tenacity
from google import genai
from google.genai import types
from src.config_loader import load_config

class ScriptGenerator:
    def __init__(self):
        self.config = load_config()
        mode = self.config.get("mode", "generate")
        print(f"DEBUG: ScriptGenerator initialized. Mode: {mode}")
        
        # Load API key from env or config
        api_key = os.getenv("GOOGLE_GEMINI_API_KEY", self.config.get("google_gemini_api_key", ""))
        self.client = genai.Client(api_key=api_key) if api_key and api_key != "YOUR_GEMINI_API_KEY" else genai.Client()

    def generate_script(self, is_longform=False):                
        # Use pregenerated script file if configured
        if self.config.get("mode") == "pregenerated":
            print(f"DEBUG: Entering pregenerated mode.")
            batch_file = self.config.get("batch_file")
            if not batch_file or not os.path.exists(batch_file):
                raise Exception(f"Pregenerated batch file not found: {batch_file}")
            
            with open(batch_file, 'r') as f:
                data = json.load(f)
            
            source = data["longform"] if is_longform else data["shortform"]
            if not source:
                raise Exception(f"⚠️ No scripts found for {'longform' if is_longform else 'shortform'} in batch file.")
            
            if is_longform:
                # Combine ALL available longform scripts for maximum duration
                print(f"🔗 Concatenating {len(source)} longform scripts for extended duration.")
                combined_script = {
                    "title": "Stoic Wisdom Deep Dive",
                    "description": "A comprehensive compilation of Stoic teachings.",
                    "hashtags": source[0].get("hashtags", ""),
                    "segments": []
                }
                for s in source:
                    combined_script["segments"].extend(s.get("segments", []))
                return combined_script
            else:
                import datetime
                day_of_year = datetime.datetime.now().timetuple().tm_yday
                idx = day_of_year % len(source)
                script = source[idx]
                print(f"📄 Loaded pregenerated shortform script index {idx}.")
                return script

        # Strict check: If not in pregenerated mode, we are allowed to generate
        print(f"DEBUG: Mode is not pregenerated. Proceeding with Gemini API generation.")
        
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
            "3. Include bracketed visual keywords [e.g., [cinematic dark aesthetic, rain on window]] before each segment.\n"
            f"4. End with a subtle call to action: 'Join the {brand} for more ancient wisdom.'\n"
            "5. If generating a long-form script, ensure it is detailed enough (at least 50 segments for a 10+ minute video).\n"
            "6. Return valid JSON with keys: 'title', 'description', 'hashtags', and 'segments' (list of {'text', 'visual_prompt'})."
        )
        
        @tenacity.retry(
            wait=tenacity.wait_exponential(multiplier=5, min=10, max=120),
            stop=tenacity.stop_after_attempt(10)
        )
        def _call_model():
            response = self.client.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7,
                ),
            )
            return json.loads(response.text)

        return _call_model()

if __name__ == "__main__":
    gen = ScriptGenerator()
    script = gen.generate_script()
    print(json.dumps(script, indent=2))
