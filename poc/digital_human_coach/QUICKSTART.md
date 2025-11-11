# Digital Human Coach - Quick Start Guide

## 🚀 Quick Setup (5 minutes)

### Step 1: Navigate to Project Directory

```powershell
cd c:\Users\Vivobook\github\digital-human\poc\digital_human_coach
```

### Step 2: Install Dependencies

```powershell
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### Step 3: Configure Environment

```powershell
# Copy example environment file
cp .env.example .env

# Edit .env with your API keys
notepad .env
```

**Minimum required for testing:**

- Set `STT_PROVIDER=whisper` (no API key needed, runs locally)
- Set `TTS_PROVIDER=edge` (no API key needed, uses Microsoft Edge TTS)
- Set `LLM_PROVIDER=openai` and add your `OPENAI_API_KEY`

### Step 4: Install FFmpeg (for video processing)

```powershell
# Using Scoop
scoop install ffmpeg

# Or download from https://ffmpeg.org/download.html
# and add to PATH
```

### Step 5: Run the Application

**Terminal 1 - Backend:**

```powershell
uv run python -m app.backend.main
```

**Terminal 2 - Frontend:**

```powershell
uv run streamlit run app/frontend/main.py
```

### Step 6: Open Your Browser

- Frontend UI: http://localhost:8501
- API Documentation: http://localhost:8000/docs

## 🎯 Try It Out

### Conversation Mode

1. Select "🗣️ Conversation" in the sidebar
2. Type a message or upload an audio file
3. Get AI feedback in real-time
4. Listen to synthesized responses

### Evaluation Mode

1. Select "📊 Evaluation" in the sidebar
2. Upload a video (MP4, AVI, MOV)
3. Click "🔍 Analyze Video"
4. Wait for processing (30-60 seconds)
5. View comprehensive feedback:
   - Speech metrics (pace, fillers, clarity)
   - Body language analysis (posture, gestures)
   - AI-generated recommendations
   - Audio feedback

## 🔧 Troubleshooting

### "Cannot import whisper"

```powershell
pip install openai-whisper
```

### "FFmpeg not found"

- Make sure FFmpeg is in your PATH
- Test: `ffmpeg -version`

### "API connection failed"

- Check backend is running on port 8000
- Verify no firewall blocking

### "Out of memory" with Whisper

- Use smaller model: Set `WHISPER_MODEL=tiny` or `WHISPER_MODEL=base`
- Or switch to cloud STT: Set `STT_PROVIDER=deepgram`

## 📝 API Keys Setup

### OpenAI (Required for LLM)

1. Visit https://platform.openai.com/api-keys
2. Create new API key
3. Add to `.env`: `OPENAI_API_KEY=sk-...`

### Deepgram (Optional, for cloud STT)

1. Visit https://console.deepgram.com/
2. Get API key
3. Add to `.env`: `DEEPGRAM_API_KEY=...`
4. Set `STT_PROVIDER=deepgram`

### ElevenLabs (Optional, for premium TTS)

1. Visit https://elevenlabs.io/
2. Get API key
3. Add to `.env`: `ELEVENLABS_API_KEY=...`
4. Set `TTS_PROVIDER=elevenlabs`

## 🎮 Testing Without API Keys

For quick testing with minimal setup:

```env
STT_PROVIDER=whisper
WHISPER_MODEL=tiny
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
TTS_PROVIDER=edge
```

This uses:

- ✅ Whisper (local, free, no API key)
- ⚠️ OpenAI (requires API key)
- ✅ Edge TTS (free, no API key)
- ✅ MediaPipe (local, free)

## 📚 Next Steps

1. **Read Documentation**: Check `docs/ARCHITECTURE.md`
2. **Explore API**: Visit http://localhost:8000/docs
3. **Customize**: Edit `app/backend/services/` for providers
4. **Test Examples**: See `examples/` folder
5. **Run Tests**: `pytest tests/`

## 🐛 Common Issues

| Issue                  | Solution                                         |
| ---------------------- | ------------------------------------------------ |
| Slow transcription     | Use `WHISPER_MODEL=tiny` or switch to `deepgram` |
| Robot-like TTS         | Upgrade to `elevenlabs` for natural voices       |
| Video processing error | Ensure FFmpeg is installed and in PATH           |
| Port already in use    | Change port in backend or kill process           |
| Import errors          | Run `pip install -e .` again                     |

## 💡 Tips

- **Faster Testing**: Use conversation mode first (quicker than video analysis)
- **Better Accuracy**: Use `WHISPER_MODEL=medium` or `large`
- **Natural Voices**: Upgrade to ElevenLabs TTS
- **Cloud Processing**: Switch to Deepgram for faster STT

## 📞 Need Help?

- Check `README.md` for full documentation
- Review `docs/ARCHITECTURE.md` for system design
- Open an issue on GitHub
- Check API logs in backend terminal

---

**Ready to coach!** 🎤🚀
