# Faceless Automation: Stoic Philosophy Video Production

An end-to-end, fully automated system for generating and publishing high-quality Stoic philosophy video content to YouTube. Leverages local Ollama LLMs, Kokoro TTS, MoviePy, and the Pexels API to create both long-form (10–20 min) and short-form (45–60 sec) videos.

## Features

### Core Capabilities
- **Dynamic Script Generation**: Uses local Ollama models (Qwen 2.5) to generate unique, compelling scripts that meet strict word count (1,300+ words for long-form, 90+ words for short-form) and segment count (12+ segments for long-form, 4+ for short-form) requirements.
- **Local Kokoro TTS**: High-quality, lightweight text-to-speech synthesis using Kokoro ONNX (no PyTorch needed). Supports American and British English voices with natural prosody.
- **Unique, Non-Repeating Footage**: Fetches unique stock video clips from Pexels API, maintains persistent ID history to prevent footage duplication across runs.
- **Smart Asset Selection**: Intelligently selects 1080p+ footage (avoiding unnecessary 4K downloads) and trims clips to 6 seconds max during preprocessing.
- **Parallel Pipeline Orchestration**: Runs long-form and short-form video generation concurrently, with proper exit code propagation and error reporting.
- **Optimized Video Rendering**: Uses FFmpeg concatenation with timestamp regeneration (`-fflags +genpts`, `setpts=PTS-STARTPTS`) to eliminate stuck frames and ensure smooth playback.
- **Intelligent Thumbnails**: Generates trendy thumbnails with compact hooks, gradient overlays, and logo placement; reads recent YouTube packaging trends to suggest clickable titles.
- **YouTube Publishing**: Integrated OAuth2 authentication for automatic uploading with metadata (title, description, tags, category).
- **QA Pipeline**: Validates generated videos (frame integrity, audio presence, TTS tag leakage) before publishing.

### Recent Updates (Oct 2026)
1. **Kokoro TTS Integration** (`src/tts.py`): Replaced Piper with Kokoro ONNX for superior audio quality and Python 3.13 compatibility.
2. **Renderer Resource Fix** (`src/renderer.py`): Changed from opening 100+ MoviePy readers simultaneously to sequential processing; added FFmpeg concatenation with timestamp regeneration to fix stuck frames.
3. **Script Validation Alignment** (`src/script_generator.py`): Long-form generation now continues until meeting **both** 1,300+ word AND 12+ segment requirements; improved error messages.
4. **Parallel Runner Robustness** (`run_all.py`): Now properly waits for both pipelines and returns nonzero exit code if either fails.
5. **Clip Processing Optimization** (`src/clip_processor.py`): Added frame rate normalization and improved FFmpeg parameters for consistent intermediate clips.
6. **Packaging Enhancements** (`src/thumbnail.py`, `src/script_generator.py`): Separate, complementary thumbnail hooks (not title-repetitive); explicit title length and clickability constraints.

---

## Prerequisites

### System Requirements
- **OS**: Windows 10/11 or macOS/Linux
- **Python**: 3.13.x
- **RAM**: 8 GB minimum (16 GB recommended for parallel processing)
- **Disk**: 50+ GB free space (for temporary video processing and model files)

### External Dependencies
1. **Ollama**: Running locally on `http://localhost:11434`
   - Download: https://ollama.ai/
   - Models: `qwen2.5-coder:3b` and `qwen2.5:3b`

2. **Pexels API Key**: Free tier available
   - Sign up: https://www.pexels.com/api/
   - Store in `config.yaml` as `pexels_api_key`

3. **YouTube OAuth Credentials**:
   - Create a Google Cloud project and enable YouTube Data API v3
   - Generate OAuth2 credentials (client_secret.json)
   - Store in project root as `client_secret.json`

4. **FFmpeg**: Required for video processing
   - Included via `imageio-ffmpeg` Python package (auto-installed)

5. **Kokoro TTS Models** (auto-downloaded on first run):
   - `kokoro-v1.0.onnx` (~325 MB) — stored in `assets/`
   - `voices-v1.0.bin` (~28 MB) — stored in `assets/`

---

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/faceless-automation.git
cd faceless-automation
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure the Project
```bash
# Copy and edit the template
cp config.template.yaml config.yaml

# Edit config.yaml with:
# - pexels_api_key (from Pexels API)
# - youtube channel_id (from YouTube Studio)
# - niche brand_name and name
```

### 5. Set Up YouTube OAuth
```bash
# Place client_secret.json in the project root
# The system will prompt you to authenticate on first upload
```

### 6. Download Kokoro Models (Optional, Auto on First Run)
```bash
# Models are auto-downloaded from GitHub releases if missing
# Manual download (if needed):
# - kokoro-v1.0.onnx: https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.onnx
# - voices-v1.0.bin: https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin
```

---

## Running the Pipelines

### Quick Start: Run Both Pipelines in Parallel
```bash
python run_all.py
```

This will:
1. Start short-form (45–60 sec Reel/Short) pipeline
2. Start long-form (10–20 min video) pipeline concurrently
3. Report success/failure for each
4. Return exit code 0 if both succeed, 1 if either fails

### Run Individual Pipelines

#### Long-Form Pipeline Only
```bash
python -m src.longform_pipeline
```
Generates a 10–20 minute long-form video, renders it, runs QA, and uploads to YouTube.

#### Short-Form Pipeline Only
```bash
python -m src.shortform_pipeline
```
Generates a 45–60 second short video, renders it, and uploads to YouTube Shorts + Instagram Reels (if configured).

#### Legacy Main Script (Full Control, Sequential)
```bash
python src/main.py
```
Runs both scripts sequentially with retry logic and parallel rendering per format.

---

## Workflow Steps

Each pipeline follows this flow:

1. **Script Generation** (Ollama)
   - Generates unique, structured narration in multiple sections
   - Validates word count and segment count
   - Extracts title, thumbnail hook, description, hashtags

2. **Voiceover Generation** (Kokoro TTS)
   - Converts narration segments to speech (24 kHz WAV)
   - Natural, high-quality output with minimal artifacts

3. **Asset Fetching** (Pexels API)
   - Searches for unique, non-repeating stock video clips
   - Maintains history to prevent duplicate footage
   - Prefers 1080p+ footage to optimize processing

4. **Clip Processing** (FFmpeg)
   - Scales/crops footage to target resolution
   - Normalizes frame rate (30 FPS)
   - Trims to 6 seconds max per clip

5. **Video Rendering** (FFmpeg + MoviePy)
   - Concatenates processed clips into seamless visual track
   - Regenerates timestamps to eliminate stuck frames
   - Overlays audio, logo, and subscribe animation
   - Outputs H.264 1080p MP4

6. **QA Validation**
   - Checks for black frames or stuck frames
   - Validates audio presence and integrity
   - Ensures no TTS tag leakage (e.g., XML markers)

7. **Thumbnail Generation** (Pillow)
   - Extracts frame at 30% mark of video
   - Adds compact hook text (2–4 words, non-repetitive of title)
   - Applies dark gradient overlay for text legibility
   - Composites logo at lower right

8. **YouTube Publishing** (OAuth2 + YouTube API)
   - Uploads video with metadata
   - Sets thumbnail
   - Publishes as public (or unlisted/private based on config)

---

## Configuration

### config.yaml
```yaml
mode: "generate"
api_base_url: "http://localhost:11434"
api_models:
  - "qwen2.5-coder:3b"
  - "qwen2.5:3b"

niche:
  name: "Stoic Philosophy & Mindset"
  brand_name: "Ancient Mindset Lab"
  target_audience: "USA 18-35 self-improvement"
  fps: 30
  resolution_longform: [1920, 1080]
  resolution_shortform: [1080, 1920]

pexels_api_key: "YOUR_KEY_HERE"

publishing:
  youtube:
    enabled: true
    client_secret_file: "client_secret.json"
    channel_id: "YOUR_CHANNEL_ID"
  instagram:
    enabled: true
    access_token: "YOUR_TOKEN"
    instagram_account_id: "YOUR_ACCOUNT_ID"
```

---

## Troubleshooting

### Stuck Frames in Video Output
**Fixed in Oct 2026 release**. If you encounter stuck frames:
- Ensure `src/renderer.py` includes `-fflags +genpts` and `setpts=PTS-STARTPTS` in the FFmpeg concat command
- Ensure `src/clip_processor.py` includes `fps={fps}` in the scale filter to normalize frame rates

### Short-Form Pipeline Fails: "Unique shots cover only X.Xs of Y.Ys audio"
- The pipeline failed to fetch enough unique footage. Options:
  1. Reduce script length (edit `src/script_generator.py` to target ~40 words instead of 90+)
  2. Increase `shot_seconds` in `src/shortform_pipeline.py` to allow longer clips
  3. Check Pexels API quota and key validity

### Ollama Connection Error
- Verify Ollama is running: `ollama serve`
- Check models are installed: `ollama list`
- Ensure `config.yaml` points to correct URL (default: `http://localhost:11434`)

### YouTube Upload Fails
- Delete `token.pickle` to force re-authentication
- Verify `client_secret.json` is valid and `channel_id` matches your channel
- Check YouTube API quota and rate limits

---

## Testing

Run the test suite to validate core functionality:
```bash
pytest -q
```

Current test coverage includes:
- Script generation word/segment validation
- Renderer shot duration allocation
- Asset ID deduplication
- Clip processing and frame rate normalization
- Thumbnail packaging

---

## Project Structure

```
faceless-automation/
├── src/
│   ├── main.py                    # Sequential pipeline orchestrator
│   ├── longform_pipeline.py       # Long-form video generation
│   ├── shortform_pipeline.py      # Short-form video generation
│   ├── script_generator.py        # Ollama-based script generation
│   ├── tts.py                     # Kokoro TTS voiceover generation
│   ├── assets.py                  # Pexels API integration
│   ├── clip_processor.py          # FFmpeg clip preprocessing
│   ├── renderer.py                # MoviePy video rendering
│   ├── thumbnail.py               # Thumbnail generation
│   ├── qa_engine.py               # QA validation
│   ├── config_loader.py           # Config file loader
│   └── publishers/
│       ├── youtube.py             # YouTube OAuth & upload
│       └── instagram.py           # Instagram Reels upload
├── run_all.py                     # Parallel pipeline runner
├── config.yaml                    # Main configuration
├── config.template.yaml           # Config template
├── requirements.txt               # Python dependencies
├── assets/                        # Kokoro models and logos
│   ├── kokoro-v1.0.onnx
│   ├── voices-v1.0.bin
│   └── logo.png
├── output/                        # Generated videos, audio, clips
├── tests/                         # Test suite
└── README.md                      # This file
```

---

## Roadmap

Planned features for future releases:
- [ ] Instagram Stories and TikTok short-form uploads
- [ ] A/B testing for titles and thumbnails
- [ ] Local Llama2 integration as alternative to Qwen
- [ ] Batch scheduling for multi-video weekly uploads
- [ ] Analytics dashboard (views, CTR, retention by video)
- [ ] Subtitle/caption generation with timing sync
- [ ] Custom voice cloning via Kokoro fine-tuning

---

## License

Apache 2.0 (see LICENSE)

---

## Contributing

Contributions are welcome. Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit changes with clear messages
4. Push to the branch
5. Open a pull request

---

## Support & Community

- Issues: https://github.com/yourusername/faceless-automation/issues
- Discussions: https://github.com/yourusername/faceless-automation/discussions

---

## Acknowledgments

- **Ollama**: Local LLM inference framework
- **Kokoro**: Open-weight TTS model (hexgrad/kokoro)
- **Pexels**: Free stock video API
- **MoviePy**: Python video editing library
- **FFmpeg**: Multimedia framework

---

**Last Updated**: 31 October 2026

Version: 1.0.0
