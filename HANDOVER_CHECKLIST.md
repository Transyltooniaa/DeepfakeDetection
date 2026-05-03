# 📋 Project Handover Checklist — DeepFake Detection System

> **Status key:** ✅ Done &nbsp;|&nbsp; ⚠️ Partial &nbsp;|&nbsp; ❌ Missing &nbsp;|&nbsp; ➡️ Next batch action

---

## 🧭 0. Project Overview

| Field | Details |
|---|---|
| **Project Title** | Real-Time Multimodal DeepFake Detection System |
| **Problem Solved** | Detects AI-generated (deepfake) video and audio in near real-time via Android camera + microphone streaming |
| **Repository** | *(add GitHub URL here)* |
| **Duration** | *(add project duration)* |
| **Guide / Mentor** | *(add mentor details)* |
| **Team Members** | *(add previous batch names)* |

---

## 📘 1. README

| Item | Status | Note |
|---|---|---|
| Project overview | ✅ | See `README.md` |
| Features list | ✅ | Table with all features |
| Tech stack | ✅ | Backend + Frontend |
| Quick start / setup | ✅ | Conda + pip instructions |
| Run instructions | ✅ | Server + Gradio |
| API reference | ✅ | All endpoints documented |
| Screenshots / demo | ⚠️ | Screenshots in `FinalReport.pdf`; add inline images to README |
| FAQ / common issues | ✅ | Common setup gotchas covered |

---

## ⚙️ 2. Requirements Documentation

### Functional Requirements ✅ (see `docs/requirements/functional.md` + `FinalReport.pdf`)

- Real-time video deepfake detection via WebSocket streaming
- Audio deepfake detection (concurrent with video)
- Single-frame and batch-frame REST endpoints
- File upload analysis (image + video)
- Face/person presence check (lightweight)
- AI watermark detection via Gemini LLM
- User feedback collection and RL-based weight adaptation
- Verdict categories: Real / Fake / Suspicious

### Non-Functional Requirements ✅

- Inference target: <10s per 15-frame batch
- Single GPU worker (model shared across requests via inference lock)
- Concurrent WebSocket clients supported via asyncio
- Security-first fusion detects split-modality attacks
- Weights and feedback persist across restarts (`rl_weights.json`, `feedback_data.jsonl`)

### Software Requirements ✅

| Layer | Stack |
|---|---|
| Language | Python 3.10, Kotlin (Android) |
| Video model | GenConViT (timm 0.6.5, torch 2.10) |
| Audio model | Wav2Vec2 (transformers 5.3, HuggingFace) |
| Web server | FastAPI 0.135 + Uvicorn 0.42 |
| Face detection | face-recognition 1.3.0, dlib |
| Optional LLM | google-genai 1.68 (Gemini) |
| Runtime env | Conda `deepfake` (Python 3.10) |

---

## 🧱 3. System Design Documentation

> 📄 See `docs/design/` and `FinalReport.pdf` for diagrams.

### High-Level Architecture

```
Android App
  │  Camera frames (JPEG) + mic audio (WAV)
  │  WebSocket / HTTP multipart
  ▼
FastAPI Server  ──────────────────────────────────────────────────────────────
  │                                                                            
  ├── /ws/analyze  (WebSocket — primary)                                       
  ├── /predict_batch  (REST — Android batch)                                   
  ├── /analyze_file   (REST — file upload)                                     
  └── /predict        (REST — single frame legacy)                             
  │
  ▼
DeepFakeDetector (orchestrator)
  ├── CvitDetector        → GenConViT (ED + VAE) → video_fake_score
  ├── AudioDetector       → Wav2Vec2             → audio_fake_score
  ├── WatermarkDetector   → Gemini LLM           → wm_detected (optional)
  └── FusionStrategy      → SecurityFirst / Weighted / Adaptive / RL
          │
          └── RLAdaptiveFusion (shadow learning from /feedback endpoint)
  │
  ▼
JSON Response → Android UI
```

### Module Breakdown

| Module | File | Responsibility |
|---|---|---|
| Orchestrator | `detector.py` | Wires all detectors + fusion |
| Video detector | `detectors/cvit_detector.py` | GenConViT batch inference, face crop, dlib |
| Audio detector | `detectors/audio_detector.py` | Wav2Vec2 pipeline |
| Watermark check | `detectors/watermark_detector.py` | Gemini frame analysis |
| Fusion | `fusion/fusion_strategy.py` | 4 fusion strategies + abstract base |
| RL system | `rl_system.py` | Gradient-based weight learning, feedback DB |
| Server | `server.py` | FastAPI + WebSocket endpoints |
| Config | `config.py` | All tuneable parameters |
| Utils | `utils/video_processor.py` | Frame extraction (OpenCV) |
| Utils | `utils/audio_processor.py` | Audio extraction (moviepy/librosa) |

---

## 🏗️ 4. Architecture Documentation

> 📄 Full architecture diagrams in `FinalReport.pdf`.

### Key Design Decisions

| Decision | Rationale |
|---|---|
| **Security-first fusion as default** | Detects split-modality attacks (face-swap + real audio) that weighted average would miss |
| **GenConViT as primary model** | State-of-the-art transformer-CNN hybrid; outperforms XceptionNet on FaceForensics++ |
| **Video weight 0.95, audio 0.05** | Audio deepfake detector is less reliable on short clips; video dominates |
| **RL in shadow mode by default** | Avoids production risk; weights are learned but only applied when `FUSION_MODE=rl_adaptive` |
| **Inference lock (single thread)** | GPU VRAM is shared; concurrent inference causes OOM on consumer GPUs |
| **WebSocket streaming** | Allows continuous analysis without per-request HTTP overhead |
| **Gemini watermark as override** | High-confidence watermark detection (>0.75) always overrides model output to Fake |

---

## 💻 5. Codebase Readiness

| Item | Status | Note |
|---|---|---|
| Clean folder structure | ✅ | `Backend/`, `frontend/`, `docs/` |
| No unnecessary files | ⚠️ | Remove `__pycache__/`, `.DS_Store` before final handover |
| Naming conventions | ✅ | Snake_case modules, PascalCase classes |
| Comments for complex logic | ✅ | Fusion strategies, RL update logic documented |
| Docstrings | ✅ | All public methods have docstrings |
| No secrets in code | ✅ | `GEMINI_API_KEY = ""` default; never committed |

---

## 📦 6. Dependency & Environment Setup

| Item | Status | File |
|---|---|---|
| pip requirements | ✅ | `Backend/requirements.txt` |
| Full pinned conda env | ✅ | `Backend/environment.yml` (Linux, Python 3.10, CUDA 12.1, torch 2.5.1+cu121) |
| `.env.example` | ✅ | Created at project root |
| Environment vars documented | ✅ | Documented in `.env.example` and `config.py` |

### Recommended `.env.example` to add:
```env
# Google Gemini API (optional — leave blank to disable)
GEMINI_API_KEY=

# Server bind settings (defaults used if unset)
HOST=0.0.0.0
PORT=7860
```

---

## 🗄️ 7. Database Documentation

This project uses **file-based storage only** (no SQL database).

| Storage | File | Purpose |
|---|---|---|
| Feedback log | `Backend/feedback_data.jsonl` | JSONL — one feedback entry per line |
| RL weights | `Backend/rl_weights.json` | Current learned video/audio weights |
| Verified media | `Backend/verified/real/` and `verified/fake/` | User-verified image/video samples |

### Feedback Entry Schema
```json
{
  "timestamp": "ISO-8601 datetime",
  "prediction": { "verdict": "FAKE", "video_fake_score": 0.82, "audio_fake_score": 0.34 },
  "user_label": "FAKE",
  "user_confidence": 1.0,
  "metadata": {}
}
```

---

## 🚀 8. Deployment Documentation

> 📄 See `docs/deployment/` for full steps.

### Local Development
```bash
conda activate deepfake
cd Backend
python server.py
```

### Production (Hugging Face Spaces / bare server)
```bash
uvicorn server:app --host 0.0.0.0 --port 7860 --workers 1
```

> ⚠️ Always use `--workers 1` — the model is not safe for multi-process GPU sharing.

### Hosting Notes
| Platform | Notes |
|---|---|
| Hugging Face Spaces | Works with Docker Space; set `PORT=7860` env var |
| Local GPU server | Recommended; CUDA 11.8+ required for torch 2.10 |
| CPU-only | Works but inference is ~10× slower |

### Environment Variables for Production
```
HOST=0.0.0.0
PORT=7860
GEMINI_API_KEY=<your-key>   # only if watermark detection needed
```

---

## 🧪 9. Testing

| Item | Status | Note |
|---|---|---|
| Unit tests | ❌ | ➡️ Priority for next batch |
| Integration tests | ❌ | ➡️ Priority for next batch |
| Manual test procedure | ✅ | See below |

### Manual Test Checklist
1. Start server: `python server.py`
2. Hit `http://localhost:7860/health` — expect `{"status":"ok"}`
3. Upload a known fake image to `/analyze_file` — expect `prediction: "Fake"`
4. Upload a known real image — expect `prediction: "Real"`
5. Open Gradio UI (`gradio_app.py`) and test via browser
6. Submit feedback to `/feedback` — check `rl_weights.json` updates

### Suggested Test Files
- Use FaceForensics++ dataset samples for ground-truth testing
- Keep a small local set of verified real/fake clips in `Backend/verified/`

---

## 🧾 10. Sprint Documentation

> 📄 Sprint records in `docs/sprints/`. See `FinalReport.pdf` for detailed sprint history.

### Sprint Summary
| Sprint | Focus | Status |
|---|---|---|
| 1 | GenConViT integration + basic API | ✅ Completed |
| 2 | Audio detector + fusion strategies | ✅ Completed |
| 3 | Android WebSocket client + real-time streaming | ✅ Completed |
| 4 | RL feedback system + Gemini watermark | ✅ Completed |
| 5 | Security-first fusion + hardening | ✅ Completed |

---

## 🛣️ 11. Roadmap & Future Work

### High Priority (Next Batch)
- [ ] Add unit tests for detector modules and fusion strategies
- [ ] Create `.env.example` and move API keys out of `config.py`
- [ ] Add Docker support (`Dockerfile` + `docker-compose.yml`)
- [ ] Implement proper database (SQLite/PostgreSQL) for feedback storage
- [ ] Add authentication to API endpoints

### Medium Priority
- [ ] Evaluate newer deepfake models (e.g., CLIP-based, ViT-L)
- [ ] Support real-time audio deepfake streaming (current: batch per cycle)
- [ ] Add explainability layer (heatmaps, attention visualization)
- [ ] Benchmark against FaceForensics++ and DFDC datasets formally

### Low Priority / Nice-to-Have
- [ ] Admin dashboard for monitoring predictions + RL weight evolution
- [ ] Batch evaluation script for offline video files
- [ ] iOS client

---

## 🐞 12. Known Issues & Limitations

| Issue | Severity | Workaround |
|---|---|---|
| `face_recognition` install fails on some systems | High | Install dlib via conda first: `conda install -c conda-forge dlib` |
| Audio analysis unreliable on clips < 2 seconds | Medium | System falls back to video-only verdict |
| GPU OOM on high-res frames | Medium | Resize frames to 224×224 before sending; set `CVIT_FP16=True` |
| No authentication on API | Medium | Deploy behind a reverse proxy (nginx) with auth |
| `feedback_data.jsonl` unbounded growth | Low | Periodically archive or prune old entries |
| Gemini watermark adds ~5s latency | Low | Runs concurrently with model; only noticeable if model is fast |
| Person detection may miss non-frontal faces | Low | Uses OpenCV Haar + HOG; replace with MTCNN for better recall |
| No HTTPS in dev server | Low | Use ngrok or nginx+certbot for production |

---

## 🎥 13. Demo & Presentation

| Item | Status | Location |
|---|---|---|
| Final Report (PDF) | ✅ | `FinalReport.pdf` |
| Presentation slides | ✅ | `Presentation.pdf` |
| Screenshots | ✅ | In `FinalReport.pdf` |

---

## 🔐 14. Access & Credentials Transfer

| Resource | Status | Action Required |
|---|---|---|
| GitHub repository | ➡️ | Transfer ownership / add next batch as collaborators |
| Hugging Face Space | ➡️ | Transfer to team org or share access token |
| Gemini API key | ⚠️ | Rotate and share securely (do NOT commit to repo) |
| GenConViT model weights | ➡️ | Upload to shared cloud storage (weights are too large for GitHub) |

> ⚠️ **Confirm:** No API keys, passwords, or tokens are committed to the repository.

---

## 🔖 15. Versioning & Releases

| Item | Status | Note |
|---|---|---|
| Version tags | ⚠️ | ➡️ Tag current state as `v1.0.0` |
| `CHANGELOG.md` | ✅ | See `CHANGELOG.md` |

---

## 🤝 16. Contribution Guidelines

### Branching Strategy
```
main          ← stable, production-ready
dev           ← active development
feature/<name> ← new features
fix/<name>    ← bug fixes
```

### Commit Message Format
```
<type>(<scope>): <short description>

Types: feat | fix | refactor | docs | test | chore
Examples:
  feat(fusion): add adaptive confidence-weighted strategy
  fix(audio): handle empty WAV files gracefully
  docs(readme): add model weight download instructions
```

### Pull Request Process
1. Branch off `dev`
2. Open PR against `dev` with description of changes
3. Ensure server starts successfully and manual test checklist passes
4. Merge only after review

---

## 🧹 17. GitHub Hygiene

| Item | Status | Action |
|---|---|---|
| Issues labeled | ➡️ | Label open issues with `bug`, `enhancement`, `question` |
| Dead branches removed | ➡️ | Delete stale feature branches |
| `.DS_Store` removed | ➡️ | Add to `.gitignore` and remove from history |

### Add to `.gitignore`:
```
**/.DS_Store
**/__pycache__/
*.pyc
.env
Backend/verified/
Backend/weight/
```

---

## ⚖️ 18. License

| Item | Status | Note |
|---|---|---|
| License file | ✅ | `frontend/LICENSE` (Apache 2.0) |

---

## 📄 19. Handover Notes

### Key Decisions Explained
- **Security-first fusion was chosen over RL fusion as the production default.** The RL system is in "shadow mode" by default — it collects feedback and learns weights, but doesn't influence predictions unless you set `FUSION_MODE=rl_adaptive`. This was intentional to avoid unpredictable behaviour during demos.
- **Video weight is set to 0.95.** The audio model (`wav2vec2-deepfake-voice-detector`) was found to be less reliable on short clips extracted from phone microphone. Do not increase audio weight without re-evaluating on your test set.
- **The inference lock (`threading.Lock`) is critical.** Do not remove it. Two concurrent requests will cause a CUDA OOM crash on most consumer GPUs.
- **Gemini watermark detection overrides model output.** If confidence > 0.75, the result is forced to Fake ~90–98%. This is intentional and tuned conservatively.

### Challenges Faced
- GenConViT requires `timm==0.6.5` specifically — newer timm versions break the model architecture loading.
- `face-recognition` + `dlib` are notoriously hard to install on Apple Silicon Macs; conda is the only reliable method.
- Android WebSocket + CameraX synchronization required careful buffer management to avoid frame drops.
- Wav2Vec2 model is slow on CPU (~3–5s per clip); a GPU is effectively required for real-time use.

### Lessons Learned
- Always pin exact versions in `environment.yml` for ML projects — even minor updates in `transformers` or `timm` can silently change model outputs.
- Security-first fusion is more robust than simple weighted averaging for adversarial inputs.
- Real-world phone audio is much noisier than dataset audio — the audio model confidence was often low, justifying the low audio weight.

### Tips for Next Batch
- Start by reading `FinalReport.pdf` end-to-end before touching the code.
- Test the server with the Gradio UI before connecting the Android app — it's much faster to iterate.
- If you want to improve accuracy, focus on the `cvit_detector.py` — the face crop + frame selection logic has room for improvement.
- The `feedback_data.jsonl` file already contains real user feedback collected during the project — use it as a training/evaluation resource.
- Consider replacing `face-recognition` with `InsightFace` — it is faster and easier to install.

### Things to Avoid
- ❌ Do not set `--workers > 1` in uvicorn — the GPU model is not multiprocess-safe.
- ❌ Do not commit `rl_weights.json` or `feedback_data.jsonl` to git if they contain real user data.
- ❌ Do not commit model weight files (`.pth`) — they are too large and are gitignored.
- ❌ Do not enable `FUSION_MODE=rl_adaptive` in production without evaluating the learned weights first.

---

## 🛠️ 20. Misc

| Item | Status | Note |
|---|---|---|
| Dockerfile | ❌ | ➡️ Recommended for next batch (see template below) |
| docker-compose | ❌ | ➡️ Optional |
| Makefile / CLI shortcuts | ❌ | ➡️ Nice-to-have |

### Suggested Dockerfile (starter)
```dockerfile
FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime

WORKDIR /app
COPY Backend/ .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 7860
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
```

---

*Generated: May 2026 — DeepFake Detection System v1.0*
