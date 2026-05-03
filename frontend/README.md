# 🛡️ DeepGuard — Android Client

> Real-time deepfake detection on your phone. Streams live screen + audio to the DeepGuard backend and shows verdicts in a draggable floating overlay — without leaving whatever app you're using.

---

## Table of Contents
- [Features](#features)
- [How It Works](#how-it-works)
- [Requirements](#requirements)
- [Build & Run](#build--run)
- [Project Structure](#project-structure)
- [Permissions Explained](#permissions-explained)
- [Usage Guide](#usage-guide)
- [Configuration](#configuration)
- [Known Issues](#known-issues)

---

## Features

| Feature | Description |
|---|---|
| 🖥️ Screen capture streaming | Captures live screen frames via MediaProjection and streams to backend |
| 🎙️ Audio analysis (optional) | Captures system/mic audio and sends alongside video for joint analysis |
| 🔴 Floating overlay | Draggable, collapsible HUD shows verdicts without leaving your current app |
| 🤖 Auto-scan mode | Automatically detects when a person is on screen and starts streaming |
| 📁 File analysis | Pick an image or video from storage and run offline deepfake detection |
| ✅ Dataset contribution | Mark analysed files as Real/Fake to contribute to the server's verified dataset |
| 📡 WebSocket streaming | Continuous, low-latency connection to backend `/ws/analyze` |
| 🔔 Foreground service | Persists in background with a persistent notification |

---

## How It Works

```
┌─────────────────────────────────────────────────────┐
│              Android App (DeepGuard)                │
│                                                     │
│  MainActivity                                       │
│   ├── Configure server URL + analysis duration      │
│   ├── Request permissions (Audio, Overlay, Screen)  │
│   ├── File analysis tab (image / video upload)      │
│   └── Launch CaptureService as foreground service   │
│                                                     │
│  CaptureService  (foreground, runs in background)   │
│   ├── IDLE     → overlay shown, nothing running     │
│   ├── SCANNING → periodic /check_person calls       │
│   │              (lightweight, no ML on device)     │
│   └── STREAMING → WebSocket to /ws/analyze          │
│        ├── VideoFrameCapturer (MediaProjection)     │
│        │   → JPEG frame every 3s → [0x01 + bytes]  │
│        ├── AudioCapturer (MediaProjection audio)    │
│        │   → WAV chunk → [0x02 + bytes]             │
│        └── StreamingClient (OkHttp WebSocket)       │
│             ← JSON result: prediction + confidence  │
│                                                     │
│  OverlayManager  (floating window overlay)          │
│   ├── 🛡️ bubble (draggable, tap to expand)          │
│   └── Panel: status, verdict, scores, controls      │
└─────────────────────────────────────────────────────┘
                          │
                 WS / HTTP REST
                          │
              ┌───────────▼──────────┐
              │   Backend (FastAPI)  │
              │   /ws/analyze        │
              │   /check_person      │
              │   /analyze_file      │
              │   /verify            │
              └──────────────────────┘
```

### Auto-Scan State Machine

```
IDLE ──[Auto ON + person?]──▶ SCANNING ──[person detected]──▶ STREAMING
  ▲                                                                │
  └──[3 consecutive no-person / manual stop]──────────────────────┘
```

---

## Requirements

| Requirement | Version |
|---|---|
| Android | API 27+ (Android 8.1 Oreo) |
| Target SDK | 34 (Android 14) |
| Kotlin | 1.9+ |
| JVM target | 17 |
| Android Studio | Hedgehog (2023.1) or newer |

### Dependencies (`app/build.gradle.kts`)
| Library | Version | Purpose |
|---|---|---|
| `androidx.core:core-ktx` | 1.12.0 | Kotlin extensions |
| `androidx.appcompat:appcompat` | 1.6.1 | Backwards compatibility |
| `androidx.activity:activity-ktx` | 1.8.2 | Activity result APIs |
| `com.squareup.okhttp3:okhttp` | 4.12.0 | WebSocket + HTTP client |
| `org.json:json` | 20231013 | JSON parsing |
| `kotlinx-coroutines-android` | 1.7.3 | Async/coroutine support |
| `material` | 1.11.0 | Material Design components |

---

## Build & Run

### 1. Open in Android Studio
```
File → Open → CyberSec/frontend/app/android/
```

### 2. Sync Gradle
Android Studio will auto-sync. If it doesn't:
```
File → Sync Project with Gradle Files
```

### 3. Connect device or start emulator
- Physical device: enable **Developer Options** → **USB Debugging**
- Emulator: API 27+ AVD

### 4. Configure server URL
In the app's main screen, enter your backend URL:
```
http://<your-server-ip>:7860
```

> For Android Emulator connecting to localhost: use `http://10.0.2.2:7860`  
> For ngrok tunnel: use `https://<ngrok-id>.ngrok.io`

### 5. Build & run
```
Run → Run 'app'   (or Shift+F10)
```

---

## Project Structure

```
android/
├── app/
│   ├── build.gradle.kts               # Dependencies + build config
│   └── src/main/
│       ├── AndroidManifest.xml        # Permissions + service declarations
│       ├── java/com/deepfake/capture/
│       │   ├── MainActivity.kt        # Main UI: settings, file analysis
│       │   ├── CaptureService.kt      # Foreground service: IDLE/SCANNING/STREAMING state machine
│       │   ├── OverlayManager.kt      # Floating overlay window (bubble + panel)
│       │   ├── StreamingClient.kt     # OkHttp WebSocket client for /ws/analyze
│       │   ├── ApiClient.kt           # REST calls: /check_person, /analyze_file, /health
│       │   ├── VideoFrameCapturer.kt  # MediaProjection → JPEG frame extraction
│       │   ├── AudioCapturer.kt       # MediaProjection audio → WAV segments
│       │   └── MediaProjectionHelper.kt  # MediaProjection lifecycle management
│       └── res/                       # Layouts, strings, drawables
├── build.gradle.kts                   # Project-level build config
├── settings.gradle.kts                # Module includes
└── gradle.properties                  # JVM args
```

### Module Responsibilities

| File | Role |
|---|---|
| `MainActivity.kt` | Entry point. Manages permissions, server URL config, file picker, file analysis UI, `/verify` submissions |
| `CaptureService.kt` | Android Foreground Service. Owns the IDLE → SCANNING → STREAMING state machine. Coordinates all capture components |
| `OverlayManager.kt` | Draws the draggable floating overlay using `TYPE_APPLICATION_OVERLAY`. Handles all UI updates from results |
| `StreamingClient.kt` | OkHttp WebSocket wrapper. Sends `[0x01 + JPEG]` and `[0x02 + WAV]` binary frames. Receives JSON results |
| `ApiClient.kt` | HTTP REST calls to `/check_person` (lightweight scan), `/health`, and `/analyze_file` |
| `VideoFrameCapturer.kt` | Uses `ImageReader` + `VirtualDisplay` from `MediaProjection` to capture screen frames as JPEG |
| `AudioCapturer.kt` | Records system audio via `MediaProjection` audio (API 29+) or `AudioRecord` fallback. Buffers WAV segments |
| `MediaProjectionHelper.kt` | Wraps `MediaProjection` token lifecycle — create, get, stop |

---

## Permissions Explained

| Permission | When Requested | Why |
|---|---|---|
| `INTERNET` | Install time | WebSocket + REST communication |
| `RECORD_AUDIO` | On first overlay start | Audio capture for deepfake detection |
| `SYSTEM_ALERT_WINDOW` | On first overlay start | Draw floating overlay over other apps |
| `FOREGROUND_SERVICE` | Install time | Keep capture running in background |
| `FOREGROUND_SERVICE_MEDIA_PROJECTION` | Install time | Required for screen capture service type |
| `POST_NOTIFICATIONS` | Runtime (Android 13+) | Persistent foreground service notification |

> ⚠️ **"Display over other apps"** must be granted manually via Settings. The app navigates there automatically on first launch.

---

## Usage Guide

### Live Overlay Mode (Primary)

1. Open the app
2. Enter your backend server URL
3. Set the **analysis duration** (slider — how many seconds of footage before each analysis)
4. Tap **Start Overlay**
5. Grant permissions when prompted (Audio → Notifications → Overlay → Screen Capture)
6. A 🛡️ bubble appears — drag it anywhere on screen
7. **Tap the bubble** to expand the control panel
8. Controls:
   - `AUTO-SCAN: ON/OFF` — automatically starts streaming when a person is detected
   - `AUDIO: ON/OFF` — include audio in analysis
   - `START` — manually start streaming
   - `STOP` — manually stop streaming
9. Results appear in the panel: `✅ REAL`, `🚨 FAKE`, or `⚠️ SUSPICIOUS` with confidence %
10. Tap `✕` to close the overlay and stop the service

### File Analysis Mode

1. In the main screen, tap **Pick Image** or **Pick Video**
2. Select a file from your gallery or file manager
3. Tap **Analyse File**
4. Results appear with verdict, confidence, frames analysed, and inference time
5. Optionally tap **Mark as Real** or **Mark as Fake** to submit to the server's verified dataset

---

## Configuration

All runtime settings are persisted via `SharedPreferences` (`deepfake_prefs`):

| Key | Default | Description |
|---|---|---|
| `server_url` | `http://10.0.2.2:7860` | Backend server URL |
| `analysis_duration` | `15` seconds | Footage window per analysis cycle |
| `audio_enabled` | `false` | Include audio in streaming analysis |
| `auto_mode` | `true` | Auto-start scanning when overlay launches |

> Settings survive app restarts and are editable from the main screen.

### Connecting via ngrok (for remote testing)

If the backend is on a remote server:
```bash
# On the server
ngrok http 7860
```
Then in the app, set the server URL to the ngrok HTTPS URL.

The `StreamingClient` automatically prepends the `ngrok-skip-browser-warning` header so the WebSocket connection is not blocked by the ngrok browser warning page.

---

## Known Issues

| Issue | Workaround |
|---|---|
| Overlay not appearing | Ensure "Display over other apps" is enabled in Settings → Apps → DeepGuard |
| Audio capture silent on API < 29 | `MediaProjection` audio requires API 29+; falls back to `AudioRecord` (mic only) |
| Screen capture prompt appears every time | Android requires fresh permission for each `MediaProjection` session |
| Emulator screen capture fails | Some AVD configs don't support `VirtualDisplay`; test on physical device |
| Server unreachable on emulator | Use `10.0.2.2` instead of `localhost` or `127.0.0.1` |
| Overlay disappears after phone restart | Restart the app — `SYSTEM_ALERT_WINDOW` is not granted across reboots on some ROMs |
| High battery drain during streaming | Expected — `MediaProjection` + continuous network is resource-intensive; reduce frame rate in `CaptureService.FRAME_INTERVAL_MS` if needed |