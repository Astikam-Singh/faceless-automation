import os
import yaml
import json
import tenacity
import itertools
from openai import OpenAI
from src.config_loader import load_config

class ScriptGenerator:
    def __init__(self):
        self.config = load_config()
        # Load multiple API keys for unified API (e.g. OpenRouter/Groq)
        self.api_keys = self.config.get("api_keys", [])
        self.key_cycle = itertools.cycle(self.api_keys)
        self.base_url = self.config.get("api_base_url", "https://api.openai.com/v1")
        # Cycle through models
        self.models = self.config.get("api_models", ["gpt-4o"])
        self.model_cycle = itertools.cycle(self.models)

    def _get_client(self):
        api_key = next(self.key_cycle)
        return OpenAI(api_key=api_key, base_url=self.base_url)

    def generate_script(self, is_longform=False):                
        brand = self.config['niche'].get('brand_name', 'Ancient Mindset Lab')
        duration_desc = "10-20 minutes" if is_longform else "40-60 seconds"
        type_desc = "long-form YouTube video" if is_longform else "Shorts/Reel"
        
        if is_longform:
            prompt = (
                f"You are an expert viral scriptwriter for '{brand}' in the '{self.config['niche']['name']}' niche. "
                f"Write a deep-dive, high-retention long-form YouTube script (duration: 10-20 minutes). "
                "CRITICAL REQUIREMENTS:\n"
                "1. MUST generate 80-100 distinct segments to ensure coverage for a 15-minute video.\n"
                "2. Pacing: Diverse arguments, psychological breakdown, historical research.\n"
                "3. Visuals: Every segment MUST have a unique, highly cinematic, and creative 'visual_prompt'.\n"
                "4. Output: Valid JSON with keys: 'title', 'description', 'hashtags', 'segments' (list of {'text', 'visual_prompt'})."
            )
        else:
            prompt = (
                f"You are an expert viral scriptwriter for '{brand}' in the '{self.config['niche']['name']}' niche. "
                f"Write a punchy, high-retention YouTube Short/Reel script (duration: 40-60 seconds). "
                "CRITICAL REQUIREMENTS:\n"
                "1. MUST have 4-6 distinct segments.\n"
                "2. Pacing: Hyper-fast, immediate hook, tight impact.\n"
                "3. Visuals: Every segment MUST have a unique, highly cinematic, and creative 'visual_prompt'.\n"
                "4. Output: Valid JSON with keys: 'title', 'description', 'hashtags', 'segments' (list of {'text', 'visual_prompt'})."
            )
        
        @tenacity.retry(
            wait=tenacity.wait_exponential(multiplier=2, min=5, max=60),
            stop=tenacity.stop_after_attempt(10)
        )
        def _call_model():
            client = self._get_client()
            # Pick next model in cycle for each attempt
            model = next(self.model_cycle)
            print(f"DEBUG: Attempting with model: {model}")
            
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": "You are a helpful assistant."},
                          {"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)

        return _call_model()
