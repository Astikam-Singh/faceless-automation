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

    @staticmethod
    def _normalize_packaging(script, brand):
        title = script.get("title")
        if isinstance(title, str):
            title = title.strip()
            brand_prefixes = (f"{brand} | ", f"{brand}: ", f"{brand} - ")
            for prefix in brand_prefixes:
                if title.lower().startswith(prefix.lower()):
                    title = title[len(prefix):].strip()
                    break
            script["title"] = title

        thumbnail_text = script.get("thumbnail_text")
        if isinstance(thumbnail_text, str):
            script["thumbnail_text"] = " ".join(thumbnail_text.split()[:7])
        return script

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
            ("The Core Problem & Context", "Break down the core psychological or philosophical dilemma clearly and analytically as an expert explainer video."),
            ("Historical Roots & Origins", "Explain how ancient thinkers analyzed this exact issue, breaking down the history step by step."),
            ("The Mechanism Behind It", "Deconstruct the underlying principles like an educational essay, explaining how human cognition and Stoic philosophy interact."),
            ("Step-by-Step Breakdown", "Provide clear, structured explanations of the framework or rules for daily application."),
            ("Common Misconceptions", "Analyze why people fail or misunderstand this concept, breaking down the nuance with concrete examples."),
            ("Synthesized Framework", "Conclude with an analytical breakdown summarizing how viewers can implement this mental model today."),
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
                    f"You are an expert video essayist and educational scriptwriter for '{brand}' "
                    f"explaining concepts in the '{niche}' niche. Write as an insightful narrator breaking down complex ideas "
                    "clearly and engagingly (like a high-end documentary or educational essay channel), avoiding generic 'Hey guys' vlogging style. "
                    "The complete video must be 10-20 minutes; this section must contain "
                    "180-240 spoken words so the complete script reaches at least 1,300 words. "
                    f"Section: {section_name}. Instructions: {section_brief} "
                    "Write natural narration, not an outline. Avoid repeating earlier sections or reusing phrases. "
                    "Ensure every segment contains completely unique sentences without repetitive transitions or filler. "
                    "For the first segment's visual_prompt, describe a dramatic close-up of a weathered "
                    "classical Stoic philosopher marble bust positioned on the right, with dark negative "
                    "space on the left; no text, coins, modern objects, or unrelated imagery. "
                    "For section 1 metadata, create YouTube packaging in the established Stoic self-improvement style. "
                    "Write a highly clickable, curiosity-driven YouTube title under 90 characters. "
                    "You MUST use high-converting formats like 'Top [N] Stoic Rules to [DESIRED OUTCOME]', "
                    "'Why You Feel [PAIN/PROBLEM] (And How Stoics Fixed It)', or '7 Things Mentally Strong People Do When [SITUATION]'. "
                    "Do not start the title with the channel or brand name. "
                    "Add 'thumbnail_text' as a punchy, emotional 3-7-word phrase for large all-caps display; "
                    "it must create a strong curiosity gap and complement rather than repeat the title. "
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
        return self._normalize_packaging(script, brand)

    def generate_script(self, is_longform=False):
        brand = self.config['niche'].get('brand_name', 'Ancient Mindset Lab')
        niche = self.config['niche']['name']
        if is_longform:
            return self._generate_longform_script(brand, niche)

        prompt = (
            f"You are an expert video essayist and educational scriptwriter for '{brand}' "
            f"explaining concepts in the '{niche}' niche. Write as an insightful narrator breaking down complex ideas "
            "clearly and engagingly (like a high-end documentary or educational essay channel), avoiding generic 'Hey guys' vlogging style. "
            "Write a punchy, high-retention YouTube Short script for 40-60 seconds. "
            "It MUST contain at least 4 distinct segments and 90+ spoken words. "
            "Use an immediate hook and tight pacing. Every segment needs a unique cinematic 'visual_prompt'. "
            "CRITICAL: Avoid any word or phrase repetition across segments. Do not repeat phrases or use summary recaps. "
            "For the first segment's visual_prompt, use a dramatic classical Stoic philosopher bust, "
            "dark cinematic lighting, and no text or unrelated objects. "
            "Title: Highly clickable and curiosity-driven, under 90 characters. "
            "Must use list/curiosity formats like 'Top 7 Stoic Rules for [Goal]', 'Why Most People Fail at [X]', "
            "or 'The 1 Stoic Habit That Changes Everything'. Do not start with the brand name. "
            "Add 'thumbnail_text' as a punchy, emotional 3-7-word phrase for large all-caps display that creates a curiosity gap. "
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
            return self._normalize_packaging(script, brand)

        return _generate_shortform()

