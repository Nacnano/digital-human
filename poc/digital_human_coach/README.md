# Digital Human Communication Coach - Proof of Concept

A multi-modal AI-powered communication coach that provides real-time conversation and post-session performance analysis.

## 🎯 Features

### A. Conversation Mode

- Real-time speech-to-text transcription
- Natural language dialogue with AI
- Text-to-speech response generation
- Avatar display with synchronized audio

### B. Evaluation Mode

- Video upload and analysis
- Speech metrics (pace, filler words, pauses, tone)
- Body posture and gesture analysis
- AI-generated feedback (text + audio)
- Comprehensive JSON summary

## 🏗️ Architecture

```
┌─────────────┐
│  Frontend   │  Streamlit UI
│  (Gradio)   │  - Audio/Video recording
└──────┬──────┘  - Session management
       │         - Feedback display
       │
┌──────▼──────┐
│   Backend   │  FastAPI Server
│   (Flask)   │  - API orchestration
└──────┬──────┘  - Session storage
       │
┌──────▼──────────────────────────┐
│      External Components         │
├──────────────┬──────────────────┤
│ STT          │ Whisper/Deepgram │
│ LLM          │ GPT/Claude/Gemini│
│              │ Typhoon/NVIDIA   │
│ TTS          │ ElevenLabs/gTTS  │
│ Pose         │ MediaPipe        │
│ Video Gen    │ D-ID/EMAGE       │
└──────────────┴──────────────────┘
```

## 📦 Installation

### Prerequisites

- Python 3.10+
- uv (recommended) or pip
- Webcam and microphone for conversation mode
- FFmpeg (for video processing)

### Setup

1. **Install uv (recommended)**

   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Install dependencies**

   ```bash
   cd poc/digital_human_app
   uv sync
   ```

   Or with pip:

   ```bash
   pip install -e .
   ```

3. **Configure environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Install FFmpeg (Windows)**
   ```powershell
   scoop install ffmpeg
   # or download from https://ffmpeg.org/download.html
   ```

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:8501
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Local Development

**Run Backend Server**

```bash
python -m uvicorn app.backend.main:app --host 0.0.0.0 --port 8000
# Server runs on http://localhost:8000
```

**Run Frontend UI**

```bash
uv run streamlit run app/frontend/main.py
# UI opens at http://localhost:8501
```

### Alternative: Gradio UI

```bash
uv run python app/frontend/gradio_app.py
```

## 📖 Usage

### Conversation Mode

1. Open the frontend UI
2. Navigate to "Conversation" tab
3. Click "Start Recording" to begin
4. Speak naturally with the AI coach
5. View real-time transcription and responses
6. Stop recording when done

### Evaluation Mode

1. Navigate to "Evaluation" tab
2. Upload a video file (MP4, AVI, MOV)
3. Click "Analyze Video"
4. Wait for processing (30-60 seconds)
5. Review AI feedback and metrics
6. Download JSON report

## 🔧 Configuration

Edit `app/config/config.yaml`:

```yaml
stt:
  provider: "deepgram" # whisper, google, deepgram

llm:
  provider: "openai" # openai, anthropic, google
  model: "gpt-4"

tts:
  provider: "elevenlabs" # elevenlabs, gtts, edge
  voice_id: "..."

pose:
  detector: "mediapipe" # mediapipe, openpose
  confidence: 0.5
```

## 📊 Evaluation Metrics

| Metric           | Description               | Target      |
| ---------------- | ------------------------- | ----------- |
| Response Latency | Time from speech to reply | < 3 seconds |
| Speech Accuracy  | Word Error Rate (WER)     | < 10%       |
| Pose Tracking    | Frame detection rate      | ≥ 80%       |
| Feedback Quality | Coherence (human-judged)  | 4/5 stars   |
| System Stability | Successful run rate       | ≥ 90%       |

## 🗂️ Project Structure

```
digital_human_coach/
├── app/
│   ├── backend/
│   │   ├── main.py              # FastAPI server
│   │   ├── api/
│   │   │   ├── conversation.py  # Conversation endpoints
│   │   │   └── evaluation.py    # Evaluation endpoints
│   │   ├── services/
│   │   │   ├── stt_service.py   # Speech-to-text
│   │   │   ├── tts_service.py   # Text-to-speech
│   │   │   ├── llm_service.py   # LLM integration
│   │   │   ├── pose_service.py  # Pose estimation
│   │   │   └── metrics_service.py # Speech metrics
│   │   └── models/
│   │       └── schemas.py       # Pydantic models
│   ├── frontend/
│   │   └── main.py              # Streamlit app
│   ├── config/
│   │   └── config.yaml          # Configuration
│   └── utils/
│       ├── video_utils.py       # Video processing
│       └── storage.py           # File management
├── tests/
│   └── test_api_integration.py  # API integration tests
├── scripts/
│   ├── verify_setup.py          # Environment verification
│   └── show_verification_summary.py # Status display
├── examples/
│   ├── conversation_example.py  # Usage example
│   └── sample_feedback.md       # Sample output
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API_REFERENCE.md
│   └── DEVELOPMENT.md
├── pyproject.toml
├── .env.example
└── README.md
```

## 🧪 Testing

### Verify Setup

```bash
python scripts/verify_setup.py
```

### Run Integration Tests

```bash
# Direct execution
python tests/test_api_integration.py

# Or with pytest
pytest tests/

# With coverage
pytest --cov=app tests/
```

### Example Usage

```bash
python examples/conversation_example.py
```

## 📚 API Documentation

Once the backend is running, visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

**Conversation**

- `POST /api/conversation/start` - Start new session
- `POST /api/conversation/speak` - Send audio chunk
- `GET /api/conversation/history` - Get conversation history

**Evaluation**

- `POST /api/evaluation/upload` - Upload video
- `POST /api/evaluation/analyze` - Analyze video
- `GET /api/evaluation/report/{session_id}` - Get feedback

## 🔐 Security & Privacy

- All API communication uses HTTPS in production
- Uploaded files are automatically deleted after 24 hours
- No personally identifiable information is stored
- User consent is required before recording

## 🚧 Development Roadmap

### Phase 1: Core Infrastructure (Weeks 1-2) ✅

- [x] Backend setup with STT/LLM/TTS integration
- [x] Basic conversation flow

### Phase 2: Video Analysis (Weeks 3-5) 🚧

- [x] MediaPipe pose estimation
- [ ] Speech metrics extraction
- [ ] Feedback generation pipeline

### Phase 3: UI & Polish (Weeks 6-7)

- [ ] Streamlit dashboard
- [ ] Real-time feedback display
- [ ] Session management

### Phase 4: Advanced Features (Weeks 8-9)

- [ ] Generative video prototype
- [ ] Multi-language support
- [ ] Custom coaching scenarios

### Phase 5: Testing & Deployment (Week 10)

- [ ] Comprehensive testing
- [ ] Performance optimization
- [ ] Documentation finalization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙋 Support

For issues or questions:

- Create a GitHub issue
- Check documentation in `/docs`
- Review example scripts in `/examples`

## 🎓 References

- [Whisper Documentation](https://github.com/openai/whisper)
- [MediaPipe Pose](https://google.github.io/mediapipe/solutions/pose.html)
- [ElevenLabs API](https://elevenlabs.io/docs)
- [FastAPI Guide](https://fastapi.tiangolo.com/)
- [Streamlit Docs](https://docs.streamlit.io/)
