import sys
sys.path.insert(0, r"c:\faceless-automation")

from src.script_generator import ScriptGenerator


def test_script_generator_can_initialize():
    generator = ScriptGenerator()
    assert generator is not None
    assert hasattr(generator, "generate_script")
    assert generator.base_url == "http://localhost:11434"
    assert generator.models[0].startswith("qwen")


def test_validate_script_rejects_too_short_output():
    generator = ScriptGenerator()
    short_script = {
        "title": "Tiny script",
        "segments": [{"text": "This is too short."}]
    }
    assert generator._validate_script(short_script, is_longform=False) is False


def test_longform_generation_builds_validated_sections(monkeypatch):
    generator = ScriptGenerator()
    calls = []

    def make_section(prompt):
        calls.append(prompt)
        text = " ".join([f"section{len(calls)}" for _ in range(220)])
        return {
            "title": "Stoic Resilience",
            "description": "A practical guide to resilience.",
            "hashtags": ["stoicism"],
            "segments": [
                {"text": text[:len(text) // 2], "visual_prompt": "Ancient marble statue"},
                {"text": text[len(text) // 2:], "visual_prompt": "Quiet mountain path"},
            ],
        }

    monkeypatch.setattr(generator, "_request_json", make_section)
    script = generator._generate_longform_script("Ancient Mindset Lab", "Stoicism")

    assert len(calls) == 6
    assert generator._validate_script(script, is_longform=True)


def test_longform_generation_adds_sections_until_word_target(monkeypatch):
    generator = ScriptGenerator()
    calls = []

    def make_section(prompt):
        calls.append(prompt)
        text = " ".join([f"narration{len(calls)}" for _ in range(200)])
        return {
            "title": "Stoic Resilience",
            "segments": [
                {"text": text[:len(text) // 2], "visual_prompt": "Ancient marble statue"},
                {"text": text[len(text) // 2:], "visual_prompt": "Quiet mountain path"},
            ],
        }

    monkeypatch.setattr(generator, "_request_json", make_section)
    script = generator._generate_longform_script("Ancient Mindset Lab", "Stoicism")

    assert len(calls) == 7
    assert generator._validate_script(script, is_longform=True)


def test_longform_generation_continues_until_segment_target(monkeypatch):
    generator = ScriptGenerator()
    calls = []

    def make_section(prompt):
        calls.append(prompt)
        segments = []
        for index in range(3):
            text = " ".join([f"narration{len(calls)}" for _ in range(220)])
            segments.append({"text": text, "visual_prompt": f"Scene {index}"})
        return {"title": "Stoic Resilience", "segments": segments}

    monkeypatch.setattr(generator, "_request_json", make_section)
    script = generator._generate_longform_script("Ancient Mindset Lab", "Stoicism")

    assert len(calls) == 4
    assert len(script["segments"]) >= 12
    assert generator._validate_script(script, is_longform=True)
