# 🛡️ DeepFake Detection System

> Real-time multimodal deepfake detection using GenConViT video analysis, Wav2Vec2 audio analysis, and a Reinforcement Learning fusion layer — served over FastAPI with WebSocket streaming to an Android client.

---

## 📌 Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Screenshots / Demo](#screenshots--demo)
- [FAQ / Common Issues](#faq--common-issues)

---

## Overview

This system detects AI-generated (deepfake) video and audio content in near real-time. It combines:

- **GenConViT** (Generative Convolutional Vision Transformer) for per-frame video analysis
- **Wav2Vec2** (HuggingFace) for audio deepfake detection
- A **Security-First Fusion** strategy that detects face-swap and voice-clone attack patterns
- An **RL-based adaptive weight** system that learns from user feedback
- A **Gemini LLM watermark detector** (optional) that identifies AI-generation watermarks

The backend exposes a **FastAPI** REST + WebSocket server. The Android frontend streams live camera frames and microphone audio to the backend, receives real-time predictions, and displays verdicts with confidence scores.

---

## Features

| Feature | Description |
|---|---|
| 🎥 Real-time video analysis | WebSocket streaming from Android → 15-frame batch inference per cycle |
| 🎙️ Audio deepfake detection | Wav2Vec2 model analyzes captured audio alongside video |
| 🔐 Security-first fusion | Detects mismatch attacks (face-swap + real audio, or voice-clone + real video) |
| 🤖 RL adaptive fusion | Learns optimal video/audio weight ratios from user feedback |
| 🖼️ Watermark detection | Gemini LLM checks frames for AI generation watermarks (Veo etc.) |
| 📁 File upload analysis | Upload image or video files for offline analysis |
| 📊 Feedback loop | Users can flag wrong predictions; system re-weights fusion accordingly |
| 📡 Gradio UI | Optional Gradio web interface for quick testing |

---

## Tech Stack

### Backend
| Component | Technology |
|---|---|
| Web framework | FastAPI + Uvicorn |
| Video model | GenConViT (ED + VAE heads) via CVIT detector |
| Audio model | `garystafford/wav2vec2-deepfake-voice-detector` (HuggingFace Transformers) |
| Face detection | `face-recognition` + dlib |
| Image processing | OpenCV, Pillow |
| Audio processing | librosa, moviepy |
| Optional LLM | Google Gemini API (`google-genai`) |
| RL system | Pure-Python gradient descent (no RL libraries) |
| Runtime | Python 3.10, Conda (`deepfake` env) |

### Frontend
| Component | Technology |
|---|---|
| Platform | Android (Kotlin) |
| Camera | CameraX |
| Networking | OkHttp WebSocket |
| Audio | Android AudioRecord |

---

## Project Structure

```
CyberSec/
├── Backend/
│   ├── server.py              # FastAPI app — REST + WebSocket endpoints
│   ├── detector.py            # Main orchestrator (DeepFakeDetector class)
│   ├── config.py              # Central configuration
│   ├── rl_system.py           # RL adaptive fusion + feedback database
│   ├── requirements.txt       # Python dependencies (pip)
│   ├── environment.yml        # Full pinned conda environment
│   ├── feedback_data.jsonl    # Persistent user feedback store
│   ├── rl_weights.json        # Saved RL fusion weights
│   ├── detectors/
│   │   ├── base_detector.py       # DetectionResult dataclass
│   │   ├── cvit_detector.py       # GenConViT video detector
│   │   ├── audio_detector.py      # Wav2Vec2 audio detector
│   │   ├── video_detector.py      # High-level video pipeline
│   │   ├── gemini_detector.py     # Gemini API detector (optional)
│   │   ├── watermark_detector.py  # LLM watermark check
│   │   ├── fusion_strategy.py     # SecurityFirst / Weighted / Max / Adaptive strategies
│   │   └── rl_system.py           # RL adaptive fusion + feedback database
│   ├── utils/
│   │   ├── video_processor.py     # Frame extraction utilities
│   │   └── audio_processor.py     # Audio extraction utilities
│   └── model/                 # GenConViT model definition files
│
├── frontend/                  # Android app source
│   └── app/
│
├── docs/                      # Project documentation
│   ├── architecture/
│   ├── design/
│   ├── requirements/
│   └── deployment/
│
├── README.md
├── HANDOVER_CHECKLIST.md
├── CHANGELOG.md
└── .gitignore
```

---

## Quick Start

### Prerequisites
- Conda (Anaconda / Miniconda)
- Python 3.10
- CUDA-capable GPU (recommended) or CPU

### 1. Clone & enter the project
```bash
git clone <repo-url>
cd CyberSec
```

### 2. Create and activate conda environment
```bash
# Option A — full pinned environment (recommended)
conda env create -f Backend/environment.yml
conda activate deepfake

# Option B — minimal install
pip install -r Backend/requirements.txt
```

### 3. Download model weights

Place GenConViT model weights in `Backend/model/`:
```
Backend/model/
├── genconvit_ed_inference.pth
└── genconvit_vae_inference.pth
```

> See `Backend/config.py` for weight filename configuration.

### 4. (Optional) Configure Gemini API
```bash
# In Backend/config.py:
GEMINI_API_KEY = "your-key-here"
USE_GEMINI = True
```

### 5. Run the server
```bash
cd Backend
python server.py
# or
uvicorn server:app --host 0.0.0.0 --port 7860 --reload
```

Server will be available at:
- REST API: `http://localhost:7860`
- WebSocket: `ws://localhost:7860/ws/analyze`
- Docs: `http://localhost:7860/docs`

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Server status |
| `/health` | GET | Health check |
| `/ws/analyze` | WebSocket | Real-time streaming analysis |
| `/predict` | POST | Single frame + audio (legacy) |
| `/predict_batch` | POST | Batch frames + audio (primary Android endpoint) |
| `/analyze_file` | POST | Upload image or video file |
| `/check_person` | POST | Lightweight face presence check |
| `/feedback` | POST | Submit user feedback for RL learning |
| `/verify` | POST | Save user-verified media to dataset |
| `/stats` | GET | Server statistics + RL weights |

Full interactive docs available at `/docs` (Swagger UI) when the server is running.

---

## Configuration

All settings are in `Backend/config.py`:

| Setting | Default | Description |
|---|---|---|
| `FUSION_MODE` | `security_first` | Fusion strategy: `security_first`, `weighted`, `max`, `adaptive`, `rl_adaptive` |
| `VIDEO_WEIGHT` | `0.95` | Video model weight in fusion |
| `AUDIO_WEIGHT` | `0.05` | Audio model weight in fusion |
| `FAKE_THRESHOLD` | `0.5` | Above this → Fake verdict |
| `MISMATCH_THRESHOLD` | `0.3` | Modality disagreement that triggers SUSPICIOUS |
| `USE_GEMINI` | `False` | Enable Gemini LLM watermark checking |
| `NUM_FRAMES_TO_EXTRACT` | `10` | Frames extracted per analysis cycle |
| `RL_LEARNING_RATE` | `0.05` | RL weight adaptation speed |

---

## Screenshots / Demo

See `FinalReport.pdf` for full system screenshots and evaluation results.

---

## FAQ / Common Issues

**Q: Server crashes on startup with `ModuleNotFoundError: face_recognition`**
> Install dlib first: `conda install -c conda-forge dlib`, then `pip install face-recognition==1.3.0`

**Q: CUDA out of memory**
> Set `CVIT_FP16 = True` in `config.py` to use half-precision inference.

**Q: Audio model downloads on first run**
> The Wav2Vec2 model is auto-downloaded from HuggingFace (~360 MB). Ensure internet access on first run.

**Q: `feedback_data.jsonl` grows large**
> This is the RL training log. It is safe to delete it — the system will recreate it. Save `rl_weights.json` separately if you want to keep learned weights.
