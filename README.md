# Faceless YouTube Shorts & Instagram Reels Automation Pipeline (100% Free Stack)

This repository contains a fully automated, monetization-compliant pipeline to generate and publish short-form videos in the **Stoic Philosophy & Mindset** niche targeting USA audiences.

## Cost Breakdown ($0/month)
- **Script Generation:** Google Gemini API (Free Tier via Google AI Studio)
- **Voiceover:** `edge-tts` (Microsoft Edge neural TTS - Free, high-quality US voices)
- **Visuals:** Pexels API & Pixabay API (Free developer tiers for HD vertical stock footage)
- **Audio & Captions:** YouTube Audio Library + Local OpenAI Whisper (Free auto-captions)
- **Rendering:** Python, MoviePy, and FFmpeg (Open source)
- **Publishing:** YouTube Data API v3 & Meta Graph API

---

## Project Structure
```
faceless-automation/
├── config.yaml
├── requirements.txt
├── .env.example
├── src/
│   ├── __init__.py
│   ├── script_generator.py
│   ├── tts.py
│   ├── assets.py
│   ├── renderer.py
│   ├── publishers/
│   │   ├── __init__.py
│   │   ├── youtube.py
│   │   └── instagram.py
│   └── main.py
└── output/
```
