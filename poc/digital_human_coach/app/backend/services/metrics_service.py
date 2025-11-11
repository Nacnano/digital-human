"""
Speech Metrics Analysis Service
"""
import re
from pathlib import Path
from typing import List, Optional, Tuple

import librosa
import numpy as np
from loguru import logger

from app.backend.models.schemas import SpeechMetrics


class MetricsService:
    """Service for analyzing speech metrics from audio and transcript"""
    
    # Common filler words in English
    FILLER_WORDS = [
        "um", "uh", "er", "ah", "like", "you know", "i mean",
        "sort of", "kind of", "actually", "basically", "literally",
        "right", "okay", "so", "well", "hmm"
    ]
    
    def __init__(self):
        logger.info("Initialized Speech Metrics Service")
    
    def analyze_speech(
        self,
        audio_path: str,
        transcript: str,
        duration: Optional[float] = None
    ) -> SpeechMetrics:
        """
        Comprehensive speech analysis
        
        Args:
            audio_path: Path to audio file
            transcript: Transcribed text
            duration: Optional duration in seconds (calculated if not provided)
        
        Returns:
            SpeechMetrics object
        """
        logger.info(f"Analyzing speech metrics for: {audio_path}")
        
        # Load audio
        y, sr = librosa.load(audio_path, sr=None)
        
        if duration is None:
            duration = len(y) / sr
        
        # Text-based metrics
        words = self._tokenize_words(transcript)
        total_words = len(words)
        filler_words, filler_count = self._count_filler_words(words)
        
        # Speaking time and pauses
        speaking_time, pause_count, avg_pause = self._analyze_pauses(y, sr)
        
        # Calculate WPM
        if speaking_time > 0:
            wpm = (total_words / speaking_time) * 60
        else:
            wpm = 0
        
        # Audio-based metrics
        volume_variation = self._calculate_volume_variation(y)
        pitch_variation = self._calculate_pitch_variation(y, sr)
        clarity_score = self._calculate_clarity_score(
            wpm, filler_count, total_words, pause_count
        )
        
        metrics = SpeechMetrics(
            words_per_minute=round(wpm, 1),
            total_words=total_words,
            speaking_time_seconds=round(speaking_time, 1),
            pause_count=pause_count,
            average_pause_duration=round(avg_pause, 2),
            filler_words_count=filler_count,
            filler_words=filler_words,
            clarity_score=clarity_score,
            volume_variation=round(volume_variation, 2),
            pitch_variation=round(pitch_variation, 2)
        )
        
        logger.info(f"Speech analysis complete: {total_words} words, "
                   f"{wpm:.1f} WPM, {filler_count} fillers")
        
        return metrics
    
    def _tokenize_words(self, text: str) -> List[str]:
        """Tokenize text into words"""
        # Remove punctuation and split
        text = re.sub(r'[^\w\s]', '', text.lower())
        words = text.split()
        return words
    
    def _count_filler_words(self, words: List[str]) -> Tuple[List[str], int]:
        """Count filler words in text"""
        found_fillers = []
        filler_count = 0
        
        for word in words:
            if word in self.FILLER_WORDS:
                found_fillers.append(word)
                filler_count += 1
        
        # Get unique fillers
        unique_fillers = list(set(found_fillers))
        
        return unique_fillers, filler_count
    
    def _analyze_pauses(
        self,
        y: np.ndarray,
        sr: int,
        silence_threshold: float = 0.02,
        min_pause_duration: float = 0.3
    ) -> Tuple[float, int, float]:
        """
        Analyze pauses in speech
        
        Returns:
            (speaking_time, pause_count, average_pause_duration)
        """
        # Calculate RMS energy
        rms = librosa.feature.rms(y=y)[0]
        
        # Identify speech/silence frames
        frame_length = 2048
        hop_length = 512
        frames_per_second = sr / hop_length
        
        is_speech = rms > silence_threshold
        
        # Find pause segments
        pauses = []
        in_pause = False
        pause_start = 0
        
        for i, speech in enumerate(is_speech):
            if not speech and not in_pause:
                # Start of pause
                in_pause = True
                pause_start = i
            elif speech and in_pause:
                # End of pause
                pause_duration = (i - pause_start) / frames_per_second
                if pause_duration >= min_pause_duration:
                    pauses.append(pause_duration)
                in_pause = False
        
        # Calculate speaking time
        speech_frames = np.sum(is_speech)
        speaking_time = speech_frames / frames_per_second
        
        # Pause statistics
        pause_count = len(pauses)
        avg_pause = np.mean(pauses) if pauses else 0
        
        return speaking_time, pause_count, avg_pause
    
    def _calculate_volume_variation(self, y: np.ndarray) -> float:
        """Calculate volume variation (coefficient of variation)"""
        rms = librosa.feature.rms(y=y)[0]
        
        if len(rms) > 0 and np.mean(rms) > 0:
            cv = np.std(rms) / np.mean(rms)
            # Normalize to 0-1 range (typical CV is 0-2)
            return min(1.0, cv / 2.0)
        
        return 0.5
    
    def _calculate_pitch_variation(self, y: np.ndarray, sr: int) -> float:
        """Calculate pitch variation"""
        try:
            # Extract pitch using pyin algorithm
            f0, voiced_flag, voiced_probs = librosa.pyin(
                y,
                fmin=librosa.note_to_hz('C2'),
                fmax=librosa.note_to_hz('C7'),
                sr=sr
            )
            
            # Filter out unvoiced frames
            f0_voiced = f0[voiced_flag]
            
            if len(f0_voiced) > 0:
                # Calculate variation
                pitch_std = np.std(f0_voiced)
                pitch_mean = np.mean(f0_voiced)
                
                if pitch_mean > 0:
                    cv = pitch_std / pitch_mean
                    # Normalize (typical CV is 0-0.5 for pitch)
                    return min(1.0, cv / 0.5)
            
            return 0.5
        except Exception as e:
            logger.warning(f"Error calculating pitch variation: {e}")
            return 0.5
    
    def _calculate_clarity_score(
        self,
        wpm: float,
        filler_count: int,
        total_words: int,
        pause_count: int
    ) -> float:
        """
        Calculate overall clarity score (0-10)
        
        Based on:
        - Speaking pace (ideal: 120-160 WPM)
        - Filler word frequency
        - Pause frequency
        """
        score = 10.0
        
        # WPM penalty
        if wpm < 100:
            score -= (100 - wpm) / 20  # Too slow
        elif wpm > 180:
            score -= (wpm - 180) / 20  # Too fast
        
        # Filler word penalty
        if total_words > 0:
            filler_ratio = filler_count / total_words
            score -= filler_ratio * 20  # Heavy penalty for fillers
        
        # Pause penalty (too many short pauses)
        speaking_time = total_words / (wpm / 60) if wpm > 0 else 1
        pauses_per_minute = (pause_count / speaking_time) * 60 if speaking_time > 0 else 0
        
        if pauses_per_minute > 20:  # More than 20 pauses per minute
            score -= (pauses_per_minute - 20) / 10
        
        return max(0, min(10, score))
    
    def generate_feedback_prompt(
        self,
        transcript: str,
        speech_metrics: SpeechMetrics,
        pose_metrics: Optional[object] = None
    ) -> str:
        """Generate prompt for LLM feedback"""
        
        prompt = f"""Please analyze this communication performance and provide detailed feedback.

## Transcript
{transcript}

## Speech Metrics
- Words per Minute: {speech_metrics.words_per_minute} (ideal: 120-160)
- Total Words: {speech_metrics.total_words}
- Speaking Time: {speech_metrics.speaking_time_seconds} seconds
- Pauses: {speech_metrics.pause_count} (avg: {speech_metrics.average_pause_duration}s)
- Filler Words: {speech_metrics.filler_words_count} ({', '.join(speech_metrics.filler_words)})
- Clarity Score: {speech_metrics.clarity_score}/10
- Volume Variation: {speech_metrics.volume_variation}
- Pitch Variation: {speech_metrics.pitch_variation}
"""
        
        if pose_metrics:
            prompt += f"""
## Body Language Metrics
- Posture Score: {pose_metrics.posture_score}/10
- Gestures: {pose_metrics.gesture_count}
- Movement Smoothness: {pose_metrics.movement_smoothness}/10
- Eye Contact: {pose_metrics.eye_contact_score}/10
- Body Openness: {pose_metrics.body_openness_score}/10
"""
        
        prompt += """
Please provide:
1. **Overall Score** (1-10)
2. **Strengths** (2-3 points)
3. **Areas for Improvement** (2-3 points)
4. **Specific Recommendations** (3-5 actionable tips)
5. **Detailed Feedback** (2-3 paragraphs)

Format your response as JSON with these keys:
- overall_score
- strengths (array)
- areas_for_improvement (array)
- specific_recommendations (array)
- detailed_feedback (string)
"""
        
        return prompt
