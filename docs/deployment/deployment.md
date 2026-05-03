# Deployment Guide

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10 | Via conda |
| CUDA | 11.8+ | For GPU inference (recommended) |
| Conda | Any recent | Miniconda or Anaconda |
| RAM | 8 GB+ | 16 GB recommended |
| VRAM | 4 GB+ | 6 GB recommended for FP32 |
| Disk | 5 GB+ | Model weights ~2 GB, conda env ~3 GB |

---

## 1. Local Development

### Step 1 — Create environment
```bash
conda env create -f Backend/environment.yml
conda activate deepfake
```

### Step 2 — Place model weights
```
Backend/model/
├── genconvit_ed_inference.pth
└── genconvit_vae_inference.pth
```

Download from the shared drive link in the project handover notes.

### Step 3 — Configure (optional)
```bash
cp .env.example .env
# Edit .env to add GEMINI_API_KEY if needed
```

### Step 4 — Run
```bash
cd Backend
python server.py
```

Server starts at `http://0.0.0.0:7860`

---

## 2. Production (Bare Server / VM)

```bash
conda activate deepfake
cd Backend
uvicorn server:app \
  --host 0.0.0.0 \
  --port 7860 \
  --workers 1 \
  --log-level info
```

> ⚠️ **Always `--workers 1`** — the GPU model is not safe to share across multiple worker processes.

### Run as background service (systemd)

```ini
# /etc/systemd/system/deepfake.service
[Unit]
Description=DeepFake Detection API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/path/to/CyberSec/Backend
ExecStart=/opt/conda/envs/deepfake/bin/uvicorn server:app --host 0.0.0.0 --port 7860 --workers 1
Restart=on-failure
Environment=PORT=7860

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable deepfake
sudo systemctl start deepfake
```

---

## 3. Hugging Face Spaces

1. Create a new **Docker Space** on Hugging Face
2. Push the `Backend/` folder contents as the Docker Space repo
3. Add a `Dockerfile` (see template in `HANDOVER_CHECKLIST.md`)
4. Set environment secrets in Space settings:
   - `GEMINI_API_KEY` (if using watermark detection)
5. Space will auto-build and expose port 7860

---

## 4. Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `7860` | Listen port |
| `GEMINI_API_KEY` | `""` | Gemini API key (leave empty to disable) |

All other settings are in `Backend/config.py`.

---

## 5. Reverse Proxy (nginx) — Optional

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:7860;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 300s;
    }
}
```

WebSocket upgrade headers are required for `/ws/analyze` to work through nginx.

---

## 6. Health Verification

After deployment, verify:

```bash
# REST health
curl http://your-server:7860/health
# Expected: {"status":"ok","models_loaded":true}

# Server info
curl http://your-server:7860/
# Expected: JSON with version, models, fusion mode

# Stats
curl http://your-server:7860/stats
```
