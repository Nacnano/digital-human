# Pitch Evaluator PoC for Kaggle

A proof-of-concept implementation of the LLM evaluation + TTS generation pipeline for pitch analysis, optimized for Kaggle notebooks.

## Overview

This PoC takes transcribed speech text (from SST) along with optional emotion/posture context and produces:

1. Structured LLM-based pitch evaluation
2. Expressive audio feedback using TTS with emotion mapping

## Features

- **LLM Evaluation**: Uses OpenAI GPT to analyze pitch quality, structure, and delivery
- **Emotion Mapping**: Converts evaluation scores to appropriate TTS voice styles
- **Kaggle Optimized**: Works entirely within Kaggle's environment
- **Audio Output**: Generates expressive MP3 feedback files

## Input Format

The system accepts JSON input with:

```json
{
  "pitch_text": "Your startup pitch transcription here...",
  "emotion_context": {
    "confidence_level": 0.7,
    "energy_level": 0.8,
    "nervousness": 0.3,
    "posture_score": 0.6
  },
  "prosody": {
    "pitch_mean": 150.0,
    "pitch_std": 25.0,
    "energy_mean": 0.65,
    "speech_rate_wpm": 145.0,
    "pause_ratio": 0.15
  }
}
```

## Output Format

Returns structured evaluation:

```json
{
  "summary": "Brief pitch assessment...",
  "scores": {
    "clarity": 8,
    "structure": 7,
    "value_prop": 9,
    "persuasiveness": 6,
    "voice_tone": 7
  },
  "feedback_bullets": ["Point 1", "Point 2", "Point 3"],
  "improvement_plan": ["Suggestion 1", "Suggestion 2"],
  "voice_style": "confident",
  "audio_file": "path/to/generated/feedback.mp3"
}
```

## Voice Style Mapping

The system maps evaluation results to TTS voice styles:

- **Confident** (scores > 7): Steady pace, lower pitch, clear articulation
- **Encouraging** (scores 5-7): Warm tone, moderate pace, supportive
- **Constructive** (scores < 5): Gentle but clear, slower pace, helpful
- **Energetic** (high energy context): Faster pace, varied intonation
- **Calm** (high nervousness detected): Slower, soothing tone

## Setup in Kaggle

1. **Install Requirements**:

```python
!pip install openai gtts pygame pydub
```

2. **Set API Key**:

```python
import os
os.environ['OPENAI_API_KEY'] = 'your-openai-api-key-here'
```

3. **Run the PoC**:

```python
from pitch_evaluator import PitchEvaluator

evaluator = PitchEvaluator()
result = evaluator.evaluate_and_synthesize(input_data)
```

## Usage Examples

### Basic Usage

```python
# Simple text-only evaluation
input_data = {
    "pitch_text": "We're building an AI-powered solution that revolutionizes customer service..."
}

result = evaluator.evaluate_and_synthesize(input_data)
print(f"Overall assessment: {result['summary']}")
```

### With Emotion Context

```python
# Include emotion and posture data
input_data = {
    "pitch_text": "Our startup focuses on sustainable energy solutions...",
    "emotion_context": {
        "confidence_level": 0.4,  # Low confidence detected
        "energy_level": 0.9,      # High energy
        "nervousness": 0.7,       # Quite nervous
        "posture_score": 0.3      # Poor posture
    }
}

result = evaluator.evaluate_and_synthesize(input_data)
# Will use "encouraging" voice style to boost confidence
```

### With Prosody Data

```python
# Include speech pattern analysis
input_data = {
    "pitch_text": "Let me tell you about our revolutionary app...",
    "prosody": {
        "pitch_mean": 180.0,      # Higher pitch (nervous?)
        "speech_rate_wpm": 200.0, # Speaking very fast
        "pause_ratio": 0.05       # Very few pauses
    }
}

result = evaluator.evaluate_and_synthesize(input_data)
# LLM will consider speaking patterns in evaluation
```

## File Structure

```
pitch_evaluator.py          # Main implementation
requirements.txt           # Package dependencies
sample_inputs.json        # Example input formats
README.md                 # This file
```

## Key Components

### 1. LLM Evaluation Engine

- Analyzes pitch content, structure, and delivery
- Incorporates emotion and prosody context
- Returns structured feedback with numeric scores

### 2. Voice Style Mapper

- Maps evaluation results to appropriate TTS styles
- Considers emotion context for voice selection
- Handles edge cases (very low/high scores)

### 3. TTS Generator

- Produces expressive audio using gTTS
- Applies voice style modifications
- Saves audio files for playback in Kaggle

## Voice Style Details

| Style            | Characteristics              | Triggers                           |
| ---------------- | ---------------------------- | ---------------------------------- |
| **Confident**    | Clear, steady, authoritative | High scores, good posture          |
| **Encouraging**  | Warm, supportive, uplifting  | Medium scores, some nervousness    |
| **Constructive** | Gentle, helpful, patient     | Low scores, high improvement needs |
| **Energetic**    | Fast, varied, enthusiastic   | High energy context                |
| **Calm**         | Slow, soothing, reassuring   | High nervousness, low confidence   |

## Limitations

- **TTS Expression**: gTTS has limited prosody control; advanced TTS would be better
- **Emotion Detection**: Relies on provided context rather than analyzing audio directly
- **Language**: Currently English-only
- **API Dependency**: Requires OpenAI API access

## Extension Ideas

1. **Advanced TTS**: Integrate with Azure/Google Cloud TTS for better prosody control
2. **Multi-language**: Add support for different languages
3. **Real-time Processing**: Stream audio input and provide live feedback
4. **Visual Feedback**: Add charts showing score breakdowns
5. **Batch Processing**: Handle multiple pitches at once

## Troubleshooting

**Audio not playing in Kaggle**: Use the provided audio file path to download and play locally.

**OpenAI API errors**: Check your API key and quota limits.

**TTS generation fails**: Ensure internet connection for gTTS API calls.

**Memory issues**: Clear audio files after processing large batches.

## Sample Output

When you run the evaluator, you'll see:

```
🎯 Pitch Evaluation Complete!
📊 Clarity: 8/10, Structure: 7/10, Value Prop: 9/10
🗣️ Voice Style: Confident
🔊 Audio saved to: /kaggle/working/pitch_feedback_confident.mp3

💡 Key Improvements:
• Add specific market size data
• Include more concrete success metrics
• Practice smoother transitions between points
```

## License

MIT License - Feel free to adapt for your digital human pipeline!
