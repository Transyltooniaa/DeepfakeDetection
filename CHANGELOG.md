# Changelog

All notable changes to the DeepFake Detection System are documented here.

Format: [Semantic Versioning](https://semver.org/) — `[version] - YYYY-MM-DD`

---

## [1.0.0] - 2026-05

### Added
- **GenConViT (CVIT) video detector** — ED + VAE dual-head architecture for per-frame deepfake scoring
- **Wav2Vec2 audio detector** — HuggingFace `garystafford/wav2vec2-deepfake-voice-detector` pipeline
- **FastAPI server** with REST + WebSocket endpoints
- **WebSocket streaming endpoint** (`/ws/analyze`) for continuous Android camera streaming
- **Batch prediction endpoint** (`/predict_batch`) — primary Android app endpoint
- **File upload analysis** (`/analyze_file`) — supports image (JPEG/PNG) and video (MP4/MOV/AVI)
- **Security-first fusion strategy** — detects face-swap and voice-clone attack patterns via modality mismatch
- **Weighted, Max, and Adaptive fusion strategies** as configurable alternatives
- **RL adaptive fusion system** — gradient-based weight learning from user feedback (shadow mode by default)
- **Feedback endpoint** (`/feedback`) — collects user corrections; persists to `feedback_data.jsonl`
- **Gemini LLM watermark detector** — checks frames for AI generation watermarks (Veo etc.)
- **Watermark override logic** — Gemini confidence > 0.75 forces Fake verdict at 90%+
- **Person/face presence check** (`/check_person`) — lightweight OpenCV detection for Android auto-start
- **Verified media storage** (`/verify`) — saves user-labeled real/fake samples to local dataset
- **Gradio web UI** (`gradio_app.py`) for browser-based testing
- **Central config module** (`config.py`) with all tuneable parameters
- **RL weight persistence** (`rl_weights.json`) — weights survive server restarts
- **Full conda environment** (`environment.yml`) with pinned dependencies

### Architecture
- Single-worker GPU-safe inference with `threading.Lock` to prevent concurrent OOM
- Async WebSocket with three concurrent tasks: receiver, analyzer, status sender
- Parallel LLM watermark check via `ThreadPoolExecutor` alongside model inference

---

## [0.3.0] - 2026-04 (pre-release)

### Added
- Android client WebSocket integration with CameraX frame streaming
- Audio chunking and WAV transmission from Android microphone

### Changed
- Switched primary fusion from weighted to security-first
- Increased video weight from 0.70 to 0.95 based on audio reliability evaluation

---

## [0.2.0] - 2026-03 (pre-release)

### Added
- RL adaptive fusion system with feedback loop
- `/feedback` endpoint and `FeedbackDatabase` JSONL store
- Gemini API integration for optional LLM-based analysis

### Fixed
- GenConViT VAE head weight loading on CPU fallback

---

## [0.1.0] - 2026-02 (initial)

### Added
- Basic FastAPI server with `/predict` endpoint
- GenConViT video model integration
- Wav2Vec2 audio model integration
- Simple weighted fusion (70% video / 30% audio)
