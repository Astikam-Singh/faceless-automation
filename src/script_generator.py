import itertools
import os
import json
import tenacity

try:
    from ollama import Client
except ImportError:  # pragma: no cover - safety for older package names
    from ollama import Ollama as Client

from src.config_loader import load_config

class ScriptGenerator:
    def __init__(self):
        self.config = load_config()
        # Force local Ollama-only usage for script generation.
        self.api_keys = []
        self.base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        default_models = ["qwen2.5-coder:3b", "qwen2.5:3b"]
        self.models = self.config.get("api_models") or default_models
        self.model_cycle = itertools.cycle(self.models)

    def _get_client(self):
        if Client is None:
            raise ImportError("The installed Ollama Python package is unavailable or incompatible with this project.")
        return Client(host=self.base_url)

    def _validate_script(self, script, is_longform=False):
        if not isinstance(script, dict):
            return False

        segments = script.get("segments", [])
        if not isinstance(segments, list):
            return False

        valid_segments = []
        for segment in segments:
            if not isinstance(segment, dict):
                continue
            text = segment.get("text")
            if isinstance(text, str) and text.strip():
                valid_segments.append(text.strip())

        if not valid_segments:
            return False

        total_words = sum(len(text.split()) for text in valid_segments)
        min_segments = 12 if is_longform else 4
        min_words = 1300 if is_longform else 90

        return len(valid_segments) >= min_segments and total_words >= min_words

    def _request_json(self, prompt):
        @tenacity.retry(
            wait=tenacity.wait_exponential(multiplier=1, min=1, max=5),
            stop=tenacity.stop_after_attempt(3),
            reraise=True,
        )
        def _call_model():
            client = self._get_client()
            model = next(self.model_cycle)
            print(f"DEBUG: Attempting with model: {model}")

            response = client.chat(
                model=model,
                messages=[{"role": "system", "content": "You are a helpful assistant."},
                          {"role": "user", "content": prompt}],
                format="json",
            )
            content = response.model_dump().get("message", {}).get("content", "")
            if not content:
                raise ValueError("Ollama returned an empty response body.")
            return json.loads(content)

        return _call_model()

    def _generate_longform_script(self, brand, niche):
        section_specs = [
            ("Opening and the central promise", "Open with a vivid hook, define the problem, and introduce the core Stoic idea."),
            ("Historical foundations", "Explain the relevant history and context accurately, without inventing quotations."),
            ("Core principles", "Develop the central principles with clear explanations and distinct examples."),
            ("Applying the principles", "Give practical, specific exercises for work, relationships, and daily setbacks."),
            ("Obstacles and real-world examples", "Address common misunderstandings, failures, and ways to recover."),
            ("Synthesis and closing", "Connect the ideas into a practical plan and end with a memorable conclusion."),
        ]
        script = {"title": "", "description": "", "hashtags": [], "segments": []}
        total_words = 0
        minimum_words = 1300
        minimum_segments = 12
        section_index = 0

        while (
            total_words < minimum_words or len(script["segments"]) < minimum_segments
        ) and section_index < 10:
            section_index += 1
            if section_index <= len(section_specs):
                section_name, section_brief = section_specs[section_index - 1]
            else:
                section_name = f"Additional practical depth {section_index - len(section_specs)}"
                covered_sections = ", ".join(name for name, _ in section_specs)
                section_brief = (
                    f"Add a new practical angle that deepens the discussion without repeating these sections: {covered_sections}. "
                    "Use concrete everyday examples and actionable guidance."
                )
            last_error = None
            for attempt in range(4):
                correction = ""
                if attempt:
                    correction = (
                        " Your previous response was too short or invalid. Return at least 100 spoken words "
                        "across 2-3 complete segments; do not summarize or use filler."
                    )
                prompt = (
                    f"You are writing section {section_index} of a spoken long-form YouTube script for '{brand}' "
                    f"about '{niche}'. The complete video must be 10-20 minutes; this section must contain "
                    "180-240 spoken words so the complete script reaches at least 1,300 words. "
                    f"Section: {section_name}. Instructions: {section_brief} "
                    "Write natural narration, not an outline. Avoid repeating earlier sections. "
                    "For section 1 metadata, write a specific, curiosity-led but accurate YouTube title "
                    "under 75 characters, plus 'thumbnail_text' of only 2-4 bold words that complements "
                    "the title instead of repeating it. Avoid generic list titles and unsupported claims. "
                    "Return valid JSON with keys 'title', 'thumbnail_text', 'description', 'hashtags', and 'segments'. "
                    "Provide 2-3 segments, each with 'text' and a distinct cinematic 'visual_prompt'. "
                    "Only spoken narration belongs in 'text'." + correction
                )
                try:
                    section = self._request_json(prompt)
                    segments = section.get("segments", []) if isinstance(section, dict) else []
                    valid_segments = [
                        segment for segment in segments
                        if isinstance(segment, dict)
                        and isinstance(segment.get("text"), str)
                        and segment["text"].strip()
                    ]
                    word_count = sum(len(segment["text"].split()) for segment in valid_segments)
                    if len(valid_segments) < 2 or word_count < 80:
                        raise ValueError(
                            f"Section {section_index} had {word_count} words across {len(valid_segments)} segments."
                        )
                    if section_index == 1:
                        script["title"] = section.get("title", "")
                        script["thumbnail_text"] = section.get("thumbnail_text", "")
                        script["description"] = section.get("description", "")
                        script["hashtags"] = section.get("hashtags", [])
                    script["segments"].extend(valid_segments)
                    total_words += word_count
                    print(
                        f"DEBUG: Long-form section {section_index}: {word_count} words "
                        f"({total_words}/1300 total)"
                    )
                    break
                except Exception as error:
                    last_error = error
                    print(f"WARNING: Long-form section {section_index} attempt {attempt + 1} failed: {error}")
            else:
                raise RuntimeError(
                    f"Ollama could not generate a valid long-form section {section_index} after 4 attempts."
                ) from last_error

        if not self._validate_script(script, is_longform=True):
            word_count = sum(
                len(segment.get("text", "").split())
                for segment in script["segments"]
                if isinstance(segment, dict)
            )
            raise RuntimeError(
                "Generated long-form script did not meet requirements: "
                f"{word_count}/{minimum_words} words and "
                f"{len(script['segments'])}/{minimum_segments} segments."
            )
        return script

    def generate_script(self, is_longform=False):
        brand = self.config['niche'].get('brand_name', 'Ancient Mindset Lab')
        niche = self.config['niche']['name']
        if is_longform:
            return self._generate_longform_script(brand, niche)

        prompt = (
            f"You are an expert viral scriptwriter for '{brand}' in the '{niche}' niche. "
            "Write a punchy, high-retention YouTube Short/Reel script for 40-60 seconds. "
            "It MUST contain at least 4 distinct segments and 90+ spoken words. "
            "Use an immediate hook and tight pacing. Every segment needs a unique cinematic 'visual_prompt'. "
            "Title: specific, curiosity-driven, and accurate to the short's main payoff, preferably under 75 characters. "
            "Add 'thumbnail_text' with 2-4 bold words that complements, not repeats, the title. "
            "Return valid JSON with keys 'title', 'thumbnail_text', 'description', 'hashtags', and 'segments' "
            "(a list of objects with 'text' and 'visual_prompt'). Do not return an outline or summary."
        )

        @tenacity.retry(
            wait=tenacity.wait_exponential(multiplier=2, min=5, max=60),
            stop=tenacity.stop_after_attempt(10),
        )
        def _generate_shortform():
            script = self._request_json(prompt)
            if not self._validate_script(script, is_longform=is_longform):
                raise ValueError("Generated short-form script is too short; retrying.")
            return script

        return _generate_shortform()

