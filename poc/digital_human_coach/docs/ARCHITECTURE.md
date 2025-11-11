# Architecture Documentation

## System Overview

The Digital Human Communication Coach is built as a modular, microservices-inspired architecture with clear separation between frontend, backend, and external service integrations.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend Layer                       │
│  ┌─────────────────┐              ┌─────────────────┐      │
│  │   Streamlit UI  │              │   Gradio UI     │      │
│  │   - Main app    │              │   - Alternative │      │
│  │   - Components  │              │   - Simpler UI  │      │
│  └────────┬────────┘              └────────┬────────┘      │
└───────────┼──────────────────────────────────┼─────────────┘
            │                                  │
            └──────────────┬───────────────────┘
                           │ HTTP/WebSocket
┌──────────────────────────▼──────────────────────────────────┐
│                      Backend Layer                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              FastAPI Application                      │  │
│  │  ┌─────────────┐        ┌──────────────┐            │  │
│  │  │  API Routes │◄───────┤  Middleware  │            │  │
│  │  │  - /converse│        │  - CORS      │            │  │
│  │  │  - /evaluate│        │  - Auth      │            │  │
│  │  └──────┬──────┘        └──────────────┘            │  │
│  └─────────┼──────────────────────────────────────────────┘  │
│            │                                                  │
│  ┌─────────▼──────────────────────────────────────────────┐  │
│  │              Service Layer                             │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐            │  │
│  │  │   STT    │  │   LLM    │  │   TTS    │            │  │
│  │  │ Service  │  │ Service  │  │ Service  │            │  │
│  │  └──────────┘  └──────────┘  └──────────┘            │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐            │  │
│  │  │   Pose   │  │ Metrics  │  │ Storage  │            │  │
│  │  │ Service  │  │ Service  │  │ Service  │            │  │
│  │  └──────────┘  └──────────┘  └──────────┘            │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│                   External Services Layer                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Deepgram │  │  OpenAI  │  │ElevenLabs│  │MediaPipe │    │
│  │  /Whisper│  │  /Claude │  │  /gTTS   │  │/OpenPose │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└───────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Frontend Layer

#### Streamlit Application

- **Purpose**: Primary user interface for interactive sessions
- **Features**:
  - Real-time audio/video recording
  - Conversation history display
  - Video upload and preview
  - Feedback visualization
  - Session management

#### Gradio Application (Alternative)

- **Purpose**: Simpler, lighter-weight interface
- **Features**:
  - Quick demos and testing
  - Easier deployment
  - Built-in examples

### 2. Backend Layer

#### FastAPI Server

- **Technology**: FastAPI with async support
- **Port**: 8000 (configurable)
- **Features**:
  - RESTful API endpoints
  - WebSocket support for real-time communication
  - Auto-generated API documentation (Swagger/ReDoc)
  - Request validation with Pydantic
  - CORS middleware for frontend integration

#### API Routes

**Conversation Endpoints**

```
POST   /api/conversation/start        # Initialize new session
POST   /api/conversation/speak        # Process audio input
POST   /api/conversation/message      # Send text message
GET    /api/conversation/history/{id} # Get session history
DELETE /api/conversation/end/{id}     # End session
WS     /ws/conversation/{id}          # WebSocket for real-time
```

**Evaluation Endpoints**

```
POST   /api/evaluation/upload         # Upload video file
POST   /api/evaluation/analyze/{id}   # Start analysis
GET    /api/evaluation/status/{id}    # Check analysis status
GET    /api/evaluation/report/{id}    # Get feedback report
GET    /api/evaluation/metrics/{id}   # Get detailed metrics
```

**Health & Management**

```
GET    /health                        # Health check
GET    /api/sessions                  # List all sessions
DELETE /api/sessions/{id}             # Delete session
```

### 3. Service Layer

#### STT Service (Speech-to-Text)

- **Interface**: Abstract base class with multiple implementations
- **Providers**:
  - **Whisper**: OpenAI's offline model (best accuracy)
  - **Deepgram**: Fast, cloud-based (best latency)
  - **Google Cloud**: Enterprise-grade
- **Features**:
  - Automatic provider selection
  - Fallback mechanisms
  - Language detection
  - Confidence scoring

#### LLM Service (Language Model)

- **Interface**: Unified API for different LLM providers
- **Providers**:
  - **OpenAI GPT-4**: Best general performance
  - **Anthropic Claude**: Strong reasoning
  - **Google Gemini**: Cost-effective
  - **Qwen Audio**: Multimodal support
- **Features**:
  - System prompt management
  - Conversation context tracking
  - Token usage monitoring
  - Streaming responses

#### TTS Service (Text-to-Speech)

- **Interface**: Streaming audio generation
- **Providers**:
  - **ElevenLabs**: Most natural voices
  - **Edge TTS**: Fast and free
  - **gTTS**: Simple fallback
  - **Coqui TTS**: Open-source local
- **Features**:
  - Voice cloning support
  - Emotion control
  - Multiple languages
  - Audio format conversion

#### Pose Service

- **Primary**: MediaPipe Pose
- **Alternative**: OpenPose
- **Capabilities**:
  - 33-point body landmark detection
  - Real-time processing (30+ FPS)
  - 3D pose estimation
  - Gesture recognition
- **Metrics Extracted**:
  - Posture alignment
  - Hand gestures frequency
  - Movement smoothness
  - Eye contact estimation
  - Body openness score

#### Metrics Service

- **Speech Analysis**:
  - Words per minute (WPM)
  - Pause detection and duration
  - Filler words count (um, uh, like)
  - Volume variation
  - Pitch analysis
  - Speech clarity score
- **Temporal Analysis**:
  - Speaking time percentage
  - Average utterance length
  - Response latency

#### Storage Service

- **Technology**: Local filesystem + SQLite
- **Features**:
  - Temporary file management
  - Session data persistence
  - Automatic cleanup (24h TTL)
  - Optional S3 integration
- **Structure**:
  ```
  temp/
  ├── sessions/
  │   ├── {session_id}/
  │   │   ├── audio/
  │   │   ├── video/
  │   │   ├── metadata.json
  │   │   └── results.json
  ```

### 4. Data Models

#### Session Model

```python
class Session(BaseModel):
    id: str
    user_id: Optional[str]
    type: Literal["conversation", "evaluation"]
    created_at: datetime
    updated_at: datetime
    status: Literal["active", "completed", "failed"]
    metadata: Dict[str, Any]
```

#### ConversationMessage

```python
class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    audio_url: Optional[str]
    timestamp: datetime
    metadata: Dict[str, Any]
```

#### EvaluationResult

```python
class EvaluationResult(BaseModel):
    session_id: str
    video_url: str
    transcript: str
    speech_metrics: SpeechMetrics
    pose_metrics: PoseMetrics
    feedback: AIFeedback
    score: float
    recommendations: List[str]
```

## Data Flow

### Conversation Mode Flow

```
1. User speaks → Frontend captures audio
2. Audio sent to /api/conversation/speak
3. Backend → STT Service → transcription
4. Transcription → LLM Service → response
5. Response → TTS Service → audio stream
6. Audio stream → Frontend → playback
7. Save to conversation history
```

### Evaluation Mode Flow

```
1. User uploads video → /api/evaluation/upload
2. Backend saves file, creates session
3. Async processing starts:
   a. Extract audio track
   b. STT Service → full transcript
   c. Metrics Service → speech analysis
   d. Pose Service → frame-by-frame analysis
   e. Aggregate metrics
4. Send to LLM with prompt:
   - Transcript
   - Metrics summary
   - Request: structured feedback
5. LLM generates:
   - Strengths
   - Areas for improvement
   - Specific recommendations
   - Score (1-10)
6. TTS generates audio feedback
7. Store results in session
8. Frontend polls /api/evaluation/status
9. When complete, fetch /api/evaluation/report
10. Display results + play audio
```

## Security Considerations

### Authentication

- API key-based for external services
- Optional JWT for multi-user scenarios
- Rate limiting on public endpoints

### Data Privacy

- No PII stored permanently
- Automatic file deletion after 24h
- Option to disable cloud services
- GDPR-compliant data handling

### API Security

- Input validation with Pydantic
- File upload size limits (100MB)
- Allowed file type restrictions
- CORS configuration
- HTTPS in production

## Performance Optimization

### Caching

- LLM prompt caching for common patterns
- Pre-loaded model weights
- Session data caching in Redis (optional)

### Async Processing

- All I/O operations are async
- Background tasks for long operations
- WebSocket for real-time updates

### Resource Management

- Connection pooling for API clients
- Temporary file cleanup
- Memory limits for video processing

## Scalability

### Current (PoC) Stage

- Single server deployment
- Local file storage
- In-memory session management

### Future Improvements

- Load balancer + multiple API servers
- Distributed file storage (S3)
- Redis for session management
- Kubernetes deployment
- Separate processing workers
- CDN for static assets

## Monitoring & Logging

### Logging

- Structured logging with Loguru
- Log levels: DEBUG, INFO, WARNING, ERROR
- Separate logs per service
- Rotation policy: daily, max 7 days

### Metrics

- Request latency per endpoint
- Success/failure rates
- External API usage tracking
- Resource utilization

### Alerting

- Failed API calls
- High error rates
- Resource exhaustion
- Unusual activity patterns

## Configuration Management

### Environment Variables

- API keys and secrets
- Service endpoints
- Feature flags
- Resource limits

### YAML Configuration

- Service provider selection
- Model parameters
- Analysis thresholds
- UI customization

### Runtime Configuration

- Dynamic model switching
- A/B testing support
- Gradual feature rollout

## Error Handling

### Strategy

1. Graceful degradation
2. Provider fallbacks
3. User-friendly error messages
4. Automatic retries with exponential backoff
5. Circuit breaker pattern for external APIs

### Error Categories

- **User Errors**: Invalid input, file format
- **System Errors**: Service unavailable, timeout
- **External Errors**: API failures, rate limits
- **Processing Errors**: Analysis failures, model errors

## Testing Strategy

### Unit Tests

- Service layer methods
- Utility functions
- Data model validation

### Integration Tests

- API endpoint testing
- External service mocking
- End-to-end workflows

### Performance Tests

- Load testing with Locust
- Latency benchmarks
- Resource usage profiling

## Deployment

### Development

```bash
uv run uvicorn app.backend.main:app --reload
uv run streamlit run app/frontend/main.py
```

### Production

```bash
docker-compose up -d
# or
gunicorn app.backend.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e .
CMD ["uvicorn", "app.backend.main:app", "--host", "0.0.0.0"]
```

## Technology Stack Summary

| Component | Technology       | Justification                    |
| --------- | ---------------- | -------------------------------- |
| Backend   | FastAPI          | Async support, auto docs, fast   |
| Frontend  | Streamlit        | Rapid prototyping, Python-native |
| STT       | Deepgram/Whisper | Accuracy vs speed tradeoff       |
| LLM       | OpenAI GPT-4     | Best reasoning, widely supported |
| TTS       | ElevenLabs       | Most natural voices              |
| Pose      | MediaPipe        | Fast, accurate, easy integration |
| Storage   | SQLite + FS      | Simple for PoC, easy migration   |
| Config    | Hydra + YAML     | Flexible, composable configs     |

## Future Enhancements

1. **Multi-language Support**: Detect and process 20+ languages
2. **Custom Voice Training**: User-specific voice models
3. **Advanced Analytics**: ML-based trend analysis
4. **Real-time Collaboration**: Multi-user coaching sessions
5. **Mobile Apps**: iOS/Android native apps
6. **VR Integration**: Immersive practice environments
7. **Gamification**: Progress tracking, achievements
8. **Integration APIs**: Zoom, Teams, Meet plugins
