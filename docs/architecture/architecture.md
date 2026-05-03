# Architecture & Design Documentation

## System Architecture

The system follows a **client-server architecture** with a Python FastAPI backend and an Android frontend.

```
┌──────────────────────────────────────────────────────────────────┐
│                        Android Client                            │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │  CameraX   │  │ AudioRecord  │  │  WebSocket / HTTP      │  │
│  │ (frames)   │  │   (audio)    │  │  OkHttp client         │  │
│  └─────┬──────┘  └──────┬───────┘  └──────────┬─────────────┘  │
│        └────────────────┴──────────────────────┘                │
└────────────────────────────────┬─────────────────────────────────┘
                                 │  WS binary frames / HTTP multipart
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (server.py)                   │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐   │
│  │  /ws/analyze    │  │ /predict_batch  │  │ /analyze_file │   │
│  │  (WebSocket)    │  │   (REST POST)   │  │  (REST POST)  │   │
│  └────────┬────────┘  └────────┬────────┘  └───────┬───────┘   │
│           └───────────────────┬┴───────────────────┘            │
│                               ▼                                  │
│              ┌────────────────────────────────┐                 │
│              │     DeepFakeDetector            │                 │
│              │       (detector.py)             │                 │
│              │                                 │                 │
│   ┌──────────┴──┐  ┌────────────┐  ┌──────────┴──┐            │
│   │CvitDetector │  │AudioDetect.│  │WatermarkDet.│            │
│   │(GenConViT)  │  │(Wav2Vec2)  │  │(Gemini LLM) │            │
│   └──────┬──────┘  └─────┬──────┘  └──────┬──────┘            │
│          └───────────────┴─────────────────┘                    │
│                               ▼                                  │
│              ┌────────────────────────────────┐                 │
│              │      FusionStrategy             │                 │
│              │  SecurityFirst (default)        │                 │
│              │  + RL Shadow Learning           │                 │
│              └────────────────────────────────┘                 │
│                               ▼                                  │
│                      JSON Response                               │
└──────────────────────────────────────────────────────────────────┘
```

## Module-Level Design

### `detector.py` — DeepFakeDetector

**Responsibility:** Orchestrate all detectors and fusion.

```
DeepFakeDetector
  ├── video_detector: CvitDetector
  ├── audio_detector: AudioDetector
  ├── gemini_detector: GeminiDetector (optional)
  ├── rl_system: RLAdaptiveFusion (always initialized, shadow by default)
  └── fusion_strategy: FusionStrategy (set by Config.FUSION_MODE)
```

**Methods:**
| Method | Input | Output |
|---|---|---|
| `analyze_video(path)` | Video file path | Detailed result dict |
| `analyze_image(pil_image)` | PIL Image | Verdict + scores |
| `analyze_audio(path)` | Audio file path | Verdict + scores |

---

### `detectors/cvit_detector.py` — CvitDetector

**Responsibility:** GenConViT batch video deepfake inference.

**Flow:**
1. Detect faces in each frame (dlib HOG + OpenCV Haar cascade)
2. Crop and resize face regions to 224×224
3. Run GenConViT ED + VAE heads on the face batch
4. Aggregate per-frame scores → single `fake_probability`

**Key parameters:**
- `net`: `'genconvit'` (both heads), `'ed'` (encoder-decoder only), or `'vae'`
- `fp16`: Enable half-precision for GPU memory savings

---

### `detectors/audio_detector.py` — AudioDetector

**Responsibility:** Wav2Vec2 audio deepfake classification.

**Flow:**
1. Load WAV via librosa (16 kHz)
2. Pass through HuggingFace pipeline (`audio-classification`)
3. Return `fake_probability` from model logits

---

### `detectors/watermark_detector.py` — check_watermark_llm

**Responsibility:** Gemini LLM frame inspection for AI watermarks.

**Flow:**
1. Encode middle frame as base64 JPEG
2. Send to Gemini with structured prompt asking for watermark detection
3. Parse structured JSON response: `watermark_detected`, `confidence`, `reasoning`
4. If confidence > 0.75 → override verdict to Fake

---

### `fusion/fusion_strategy.py` — Fusion Strategies

| Strategy | Class | Logic |
|---|---|---|
| `security_first` | `SecurityFirstFusionStrategy` | Detects mismatch; conservative max for disagreements |
| `weighted` | `WeightedFusionStrategy` | Fixed weight average (video_w + audio_w = 1.0) |
| `max` | `MaxFusionStrategy` | Takes the higher fake probability |
| `adaptive` | `AdaptiveFusionStrategy` | Weights proportional to model confidence |
| `rl_adaptive` | `RLAdaptiveFusion` | Gradient-learned weights from user feedback |

**Security-First Fusion — Decision Matrix:**

| Video | Audio | Disagreement | Result |
|---|---|---|---|
| Fake | Fake | Any | Weighted avg → FAKE (full deepfake) |
| Real | Real | Any | Weighted avg → REAL |
| Fake | Real | > 0.3 | Max → SUSPICIOUS (face swap detected) |
| Real | Fake | > 0.3 | Max → SUSPICIOUS (voice clone detected) |
| Mixed | Mixed | 0.2–0.3 | Max → low confidence SUSPICIOUS |

---

### `rl_system.py` — RLAdaptiveFusion + FeedbackDatabase

**Responsibility:** Learn optimal fusion weights from user corrections.

**Learning rule (gradient-based):**
```
if video was more accurate:
    video_weight += lr * user_confidence   (clipped to [0.5, 0.95])
else:
    video_weight -= lr * user_confidence
audio_weight = 1.0 - video_weight
```

**Shadow mode:** When `FUSION_MODE != 'rl_adaptive'`, weights are still updated and saved, but don't influence predictions. This allows safe weight observation before enabling.

---

## Data Flow — WebSocket Analysis Cycle

```
1. Android sends config message:  {"type":"config","duration":15,"audio_enabled":false}
2. Android streams binary frames: [0x01][JPEG bytes]
3. Android streams audio chunks:  [0x02][WAV bytes]
4. Server buffers up to 200 frames, keeps latest audio
5. After `duration` seconds, server grabs buffered data
6. Parallel execution:
   a. GenConViT inference on up to 15 subsampled frames
   b. Gemini watermark check on middle frame (if enabled)
7. Fusion → verdict
8. Server sends result: {"type":"result","prediction":"Fake","confidence":0.91,...}
9. Server sends status every 2s: {"type":"status","frames_buffered":12,...}
```

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Security-first default | Simple weighted average is fooled by split-modality attacks |
| `inference_lock` (threading) | GPU model is not thread-safe; concurrent requests cause OOM |
| WebSocket over polling | Allows continuous analysis; ~60% lower latency vs HTTP polling |
| RL in shadow mode | Avoids production instability; weights observed before activation |
| Video weight 0.95 | Audio model degrades significantly on short phone mic clips |
| Gemini runs in parallel | Model inference and LLM watermark check overlap; no added latency |
