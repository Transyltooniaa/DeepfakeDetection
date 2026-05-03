# Functional Requirements

## FR-01: Real-Time Video Deepfake Detection
- The system SHALL analyze live video streams from the Android camera
- The system SHALL process frames in batches over a WebSocket connection
- The system SHALL return a prediction verdict (Real / Fake / Suspicious) within 15 seconds per analysis cycle
- The system SHALL analyze a minimum of 3 frames per cycle; up to 15 frames are subsampled from the buffer

## FR-02: Audio Deepfake Detection
- The system SHALL analyze audio captured from the Android microphone concurrently with video
- The system SHALL accept WAV audio segments and output a fake probability score
- The system SHALL gracefully degrade to video-only mode if audio is missing or too short (<200 bytes)

## FR-03: File Upload Analysis
- The system SHALL accept uploaded image files (JPEG, PNG, WEBP) for single-frame analysis
- The system SHALL accept uploaded video files (MP4, MOV, AVI, MKV, WEBM) and extract up to 15 evenly-spaced frames
- The system SHALL return prediction, confidence, fake probability, and person detection status

## FR-04: Face / Person Presence Detection
- The system SHALL detect whether a person is present in a frame using lightweight OpenCV methods
- The Android app SHALL use this to automatically start/stop the scanning session

## FR-05: Multimodal Fusion
- The system SHALL combine video and audio scores using one of: SecurityFirst, Weighted, Max, Adaptive, or RL Adaptive strategies
- The system SHALL detect modality mismatch (face-swap with real audio, voice-clone with real video) and flag as Suspicious
- The active fusion strategy SHALL be configurable without code changes

## FR-06: AI Watermark Detection
- The system SHALL optionally query the Gemini LLM with a video frame to detect AI-generation watermarks
- The system SHALL override the model verdict to Fake (90%+) if watermark confidence exceeds 0.75

## FR-07: User Feedback & RL Learning
- The system SHALL expose an endpoint to accept user feedback (correct label + confidence)
- The system SHALL persist all feedback to a JSONL file for auditability
- The system SHALL update video/audio fusion weights using gradient-based RL learning
- The system SHALL save learned weights to disk after each feedback submission

## FR-08: Verified Dataset Collection
- The system SHALL allow users to submit labeled media (real/fake) via the `/verify` endpoint
- Submitted files SHALL be stored in a local folder structure (`verified/real/`, `verified/fake/`)

## FR-09: API & Monitoring
- The system SHALL expose a health check endpoint (`/health`)
- The system SHALL expose a statistics endpoint (`/stats`) with request counts, avg inference time, and current RL weights
- The system SHALL serve interactive API documentation at `/docs`
