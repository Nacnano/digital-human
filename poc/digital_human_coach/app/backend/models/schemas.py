"""
Pydantic models and schemas for API requests and responses
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SessionType(str, Enum):
    """Session type enumeration"""
    CONVERSATION = "conversation"
    EVALUATION = "evaluation"


class SessionStatus(str, Enum):
    """Session status enumeration"""
    ACTIVE = "active"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MessageRole(str, Enum):
    """Message role in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# ============================================================================
# Session Models
# ============================================================================

class Session(BaseModel):
    """Base session model"""
    id: str
    user_id: Optional[str] = None
    type: SessionType
    created_at: datetime
    updated_at: datetime
    status: SessionStatus
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SessionCreate(BaseModel):
    """Request model for creating a session"""
    user_id: Optional[str] = None
    type: SessionType
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SessionResponse(BaseModel):
    """Response model for session"""
    id: str
    type: SessionType
    status: SessionStatus
    created_at: datetime


# ============================================================================
# Conversation Models
# ============================================================================

class ConversationMessage(BaseModel):
    """Single message in conversation"""
    role: MessageRole
    content: str
    audio_url: Optional[str] = None
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationMessageCreate(BaseModel):
    """Request to create a conversation message"""
    content: Optional[str] = None
    audio_data: Optional[str] = None  # Base64 encoded audio


class ConversationHistory(BaseModel):
    """Conversation history response"""
    session_id: str
    messages: List[ConversationMessage]
    total_messages: int


class ConversationResponse(BaseModel):
    """Response from conversation endpoint"""
    message: ConversationMessage
    audio_url: Optional[str] = None
    processing_time: float


# ============================================================================
# Evaluation Models
# ============================================================================

class SpeechMetrics(BaseModel):
    """Speech analysis metrics"""
    words_per_minute: float
    total_words: int
    speaking_time_seconds: float
    pause_count: int
    average_pause_duration: float
    filler_words_count: int
    filler_words: List[str] = Field(default_factory=list)
    clarity_score: float = Field(ge=0, le=10)
    volume_variation: float
    pitch_variation: float


class PoseMetrics(BaseModel):
    """Body pose analysis metrics"""
    posture_score: float = Field(ge=0, le=10)
    gesture_count: int
    movement_smoothness: float = Field(ge=0, le=10)
    eye_contact_score: float = Field(ge=0, le=10)
    body_openness_score: float = Field(ge=0, le=10)
    frames_analyzed: int
    tracking_quality: float = Field(ge=0, le=1)


class AIFeedback(BaseModel):
    """AI-generated feedback"""
    overall_score: float = Field(ge=0, le=10)
    strengths: List[str]
    areas_for_improvement: List[str]
    specific_recommendations: List[str]
    detailed_feedback: str
    audio_feedback_url: Optional[str] = None


class EvaluationResult(BaseModel):
    """Complete evaluation result"""
    session_id: str
    video_url: str
    transcript: str
    duration_seconds: float
    speech_metrics: SpeechMetrics
    pose_metrics: PoseMetrics
    feedback: AIFeedback
    created_at: datetime


class EvaluationStatus(BaseModel):
    """Status of evaluation processing"""
    session_id: str
    status: SessionStatus
    progress: float = Field(ge=0, le=100)
    message: str
    estimated_time_remaining: Optional[float] = None


class VideoUploadResponse(BaseModel):
    """Response after video upload"""
    session_id: str
    video_url: str
    file_size: int
    duration_seconds: Optional[float] = None
    status: str


# ============================================================================
# Error Models
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    status_code: int


# ============================================================================
# Configuration Models
# ============================================================================

class ServiceConfig(BaseModel):
    """Base service configuration"""
    provider: str
    api_key: Optional[str] = None
    model: Optional[str] = None


class STTConfig(ServiceConfig):
    """Speech-to-text configuration"""
    language: str = "en"
    enable_punctuation: bool = True


class LLMConfig(ServiceConfig):
    """Language model configuration"""
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=500, ge=1)
    system_prompt: Optional[str] = None


class TTSConfig(ServiceConfig):
    """Text-to-speech configuration"""
    voice_id: Optional[str] = None
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    emotion: Optional[str] = None


class PoseConfig(BaseModel):
    """Pose estimation configuration"""
    detector: str = "mediapipe"
    confidence_threshold: float = Field(default=0.5, ge=0, le=1)
    enable_3d: bool = False
