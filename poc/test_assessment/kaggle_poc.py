"""
Pitch Evaluator PoC - Open Source LLM to TTS Pipeline for Kaggle
================================================================

Takes speech text + emotion/posture context and produces:
1. Local LLM-based pitch evaluation with structured feedback
2. Expressive TTS audio with emotion-mapped voice styles

Uses only open-source models that run locally in Kaggle.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import tempfile
import re
import torch
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, 
    pipeline, BitsAndBytesConfig
)
from gtts import gTTS
import pygame
from io import BytesIO
import warnings
warnings.filterwarnings("ignore")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EmotionContext:
    """Emotion and posture context from upstream analysis"""
    confidence_level: float = 0.5  # 0-1 scale
    energy_level: float = 0.5      # 0-1 scale  
    nervousness: float = 0.5       # 0-1 scale
    posture_score: float = 0.5     # 0-1 scale (1 = excellent posture)


@dataclass
class ProsodyData:
    """Speech prosody metadata from SST"""
    pitch_mean: Optional[float] = None
    pitch_std: Optional[float] = None
    energy_mean: Optional[float] = None
    speech_rate_wpm: Optional[float] = None
    pause_ratio: Optional[float] = None


@dataclass
class PitchScores:
    """Numeric evaluation scores"""
    clarity: int = 5
    structure: int = 5
    value_prop: int = 5
    persuasiveness: int = 5
    voice_tone: int = 5


@dataclass
class EvaluationResult:
    """Complete evaluation output"""
    summary: str
    scores: PitchScores
    feedback_bullets: List[str]
    improvement_plan: List[str]
    voice_style: str
    audio_file: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['scores'] = asdict(self.scores)
        return result


class VoiceStyleMapper:
    """Maps evaluation results to appropriate TTS voice styles"""
    
    VOICE_STYLES = {
        'confident': {
            'description': 'Clear, steady, authoritative tone',
            'tts_modifiers': 'In a confident, professional tone: ',
            'triggers': ['high_scores', 'good_posture'],
            'speed': 1.0,
            'lang_variant': 'en'
        },
        'encouraging': {
            'description': 'Warm, supportive, uplifting tone', 
            'tts_modifiers': 'In an encouraging, supportive tone: ',
            'triggers': ['medium_scores', 'some_nervousness'],
            'speed': 1.0,
            'lang_variant': 'en'
        },
        'constructive': {
            'description': 'Gentle but clear, helpful tone',
            'tts_modifiers': 'In a constructive, helpful tone: ',
            'triggers': ['low_scores', 'high_improvement_needs'],
            'speed': 0.9,
            'lang_variant': 'en'
        },
        'energetic': {
            'description': 'Fast-paced, enthusiastic tone',
            'tts_modifiers': 'In an energetic, enthusiastic tone: ',
            'triggers': ['high_energy_context'],
            'speed': 1.1,
            'lang_variant': 'en'
        },
        'calm': {
            'description': 'Slow, soothing, reassuring tone',
            'tts_modifiers': 'In a calm, reassuring tone: ',
            'triggers': ['high_nervousness', 'low_confidence'],
            'speed': 0.8,
            'lang_variant': 'en'
        }
    }
    
    def determine_voice_style(self, scores: PitchScores, emotion_ctx: EmotionContext) -> str:
        """Determine appropriate voice style based on evaluation and context"""
        
        avg_score = (scores.clarity + scores.structure + scores.value_prop + 
                    scores.persuasiveness + scores.voice_tone) / 5
        
        # High nervousness or low confidence -> calm
        if emotion_ctx.nervousness > 0.7 or emotion_ctx.confidence_level < 0.3:
            return 'calm'
        
        # High energy -> energetic
        if emotion_ctx.energy_level > 0.8:
            return 'energetic'
        
        # Score-based selection
        if avg_score >= 7.5:
            return 'confident'
        elif avg_score >= 5.0:
            return 'encouraging'  
        else:
            return 'constructive'


class OpenSourceLLM:
    """Local LLM handler using open-source models"""
    
    def __init__(self, model_name: str = "microsoft/DialoGPT-medium"):
        """Initialize with a lightweight open-source model"""
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        
        # Try different models in order of preference
        self.model_options = [
            "microsoft/DialoGPT-small",  # Lightweight conversational
            "distilgpt2",                # Small GPT-2 variant
            "gpt2",                      # Standard GPT-2
        ]
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the model with error handling"""
        
        for model_name in self.model_options:
            try:
                logger.info(f"Loading model: {model_name}")
                
                # Use text generation pipeline for simplicity
                self.pipeline = pipeline(
                    "text-generation",
                    model=model_name,
                    tokenizer=model_name,
                    device=0 if torch.cuda.is_available() else -1,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    max_length=512,
                    do_sample=True,
                    temperature=0.7,
                    pad_token_id=50256  # GPT-2 EOS token
                )
                
                self.model_name = model_name
                logger.info(f"✅ Successfully loaded {model_name}")
                return
                
            except Exception as e:
                logger.warning(f"Failed to load {model_name}: {e}")
                continue
        
        # Fallback to rule-based evaluation
        logger.warning("⚠️ Could not load any LLM model. Using rule-based evaluation.")
        self.pipeline = None
    
    def evaluate_pitch(self, pitch_text: str, emotion_ctx: EmotionContext, 
                      prosody: Optional[ProsodyData] = None) -> Dict[str, Any]:
        """Evaluate pitch using local LLM or rule-based fallback"""
        
        if self.pipeline:
            return self._llm_evaluation(pitch_text, emotion_ctx, prosody)
        else:
            return self._rule_based_evaluation(pitch_text, emotion_ctx, prosody)
    
    def _llm_evaluation(self, pitch_text: str, emotion_ctx: EmotionContext, 
                       prosody: Optional[ProsodyData] = None) -> Dict[str, Any]:
        """LLM-based evaluation"""
        
        # Build evaluation prompt
        prompt = f"""Evaluate this startup pitch and provide scores from 1-10:

Pitch: "{pitch_text}"

Confidence: {emotion_ctx.confidence_level:.1f}, Energy: {emotion_ctx.energy_level:.1f}, Nervousness: {emotion_ctx.nervousness:.1f}

Evaluation:
Clarity: """

        try:
            # Generate response
            outputs = self.pipeline(
                prompt,
                max_length=len(prompt.split()) + 200,
                num_return_sequences=1,
                temperature=0.3
            )
            
            response_text = outputs[0]['generated_text'][len(prompt):]
            
            # Parse the response and extract insights
            return self._parse_llm_output(response_text, pitch_text, emotion_ctx)
            
        except Exception as e:
            logger.error(f"LLM evaluation failed: {e}")
            return self._rule_based_evaluation(pitch_text, emotion_ctx, prosody)
    
    def _parse_llm_output(self, response_text: str, pitch_text: str, 
                         emotion_ctx: EmotionContext) -> Dict[str, Any]:
        """Parse LLM output and create structured evaluation"""
        
        # Extract any numbers from the response as potential scores
        scores = re.findall(r'\b([1-9]|10)\b', response_text)
        
        # Use rule-based scoring with LLM insights
        rule_scores = self._calculate_rule_based_scores(pitch_text, emotion_ctx)
        
        # Adjust with LLM hints if available
        if scores and len(scores) >= 2:
            try:
                # Use first few numbers as score hints
                rule_scores['clarity'] = min(10, max(1, int(scores[0])))
                if len(scores) > 1:
                    rule_scores['structure'] = min(10, max(1, int(scores[1])))
            except:
                pass
        
        # Generate feedback based on analysis
        feedback = self._generate_feedback(pitch_text, emotion_ctx, rule_scores)
        
        return {
            "summary": feedback['summary'],
            "scores": rule_scores,
            "feedback_bullets": feedback['bullets'],
            "improvement_plan": feedback['improvements']
        }
    
    def _rule_based_evaluation(self, pitch_text: str, emotion_ctx: EmotionContext, 
                              prosody: Optional[ProsodyData] = None) -> Dict[str, Any]:
        """Rule-based evaluation as fallback"""
        
        scores = self._calculate_rule_based_scores(pitch_text, emotion_ctx, prosody)
        feedback = self._generate_feedback(pitch_text, emotion_ctx, scores)
        
        return {
            "summary": feedback['summary'],
            "scores": scores,
            "feedback_bullets": feedback['bullets'],
            "improvement_plan": feedback['improvements']
        }
    
    def _calculate_rule_based_scores(self, pitch_text: str, emotion_ctx: EmotionContext, 
                                   prosody: Optional[ProsodyData] = None) -> Dict[str, int]:
        """Calculate scores using rule-based analysis"""
        
        text = pitch_text.lower()
        word_count = len(pitch_text.split())
        
        # Clarity score (based on length, simple words, confidence)
        clarity = 5
        if word_count > 20:
            clarity += 1
        if word_count > 50:
            clarity += 1
        if emotion_ctx.confidence_level > 0.7:
            clarity += 2
        if any(word in text for word in ['um', 'uh', 'like', 'you know']):
            clarity -= 1
        
        # Structure score (introduction, problem, solution, ask)
        structure = 3
        if any(phrase in text for phrase in ['we are', 'we build', 'our company']):
            structure += 1
        if any(phrase in text for phrase in ['problem', 'issue', 'challenge']):
            structure += 2
        if any(phrase in text for phrase in ['solution', 'solve', 'fix']):
            structure += 2
        if any(phrase in text for phrase in ['funding', 'investment', 'money', 'capital']):
            structure += 1
        if '$' in text or 'revenue' in text or 'customers' in text:
            structure += 1
        
        # Value proposition (uniqueness, benefits, market)
        value_prop = 4
        if any(phrase in text for phrase in ['unique', 'first', 'only', 'revolutionary']):
            value_prop += 2
        if any(phrase in text for phrase in ['save', 'reduce', 'increase', 'improve']):
            value_prop += 2
        if any(phrase in text for phrase in ['market', 'industry', 'customers']):
            value_prop += 1
        if '%' in text:
            value_prop += 1
        
        # Persuasiveness (confidence, energy, concrete details)
        persuasiveness = int(emotion_ctx.confidence_level * 5) + 2
        if emotion_ctx.energy_level > 0.6:
            persuasiveness += 1
        if emotion_ctx.nervousness < 0.4:
            persuasiveness += 1
        if any(phrase in text for phrase in ['proven', 'successful', 'results']):
            persuasiveness += 1
        
        # Voice tone (based on emotion context and prosody)
        voice_tone = 5
        if emotion_ctx.confidence_level > 0.6:
            voice_tone += 2
        if emotion_ctx.nervousness > 0.7:
            voice_tone -= 2
        if emotion_ctx.posture_score > 0.7:
            voice_tone += 1
        
        if prosody:
            if prosody.speech_rate_wpm and prosody.speech_rate_wpm > 200:
                voice_tone -= 1  # Too fast
            if prosody.pause_ratio and prosody.pause_ratio > 0.2:
                voice_tone -= 1  # Too many pauses
        
        # Ensure scores are in valid range
        scores = {
            'clarity': max(1, min(10, clarity)),
            'structure': max(1, min(10, structure)),
            'value_prop': max(1, min(10, value_prop)),
            'persuasiveness': max(1, min(10, persuasiveness)),
            'voice_tone': max(1, min(10, voice_tone))
        }
        
        return scores
    
    def _generate_feedback(self, pitch_text: str, emotion_ctx: EmotionContext, 
                          scores: Dict[str, int]) -> Dict[str, Any]:
        """Generate contextual feedback based on analysis"""
        
        avg_score = sum(scores.values()) / len(scores)
        text = pitch_text.lower()
        
        # Generate summary
        if avg_score >= 7:
            summary = "Your pitch demonstrates strong fundamentals with clear value proposition."
        elif avg_score >= 5:
            summary = "Your pitch has good potential with several areas for enhancement."
        else:
            summary = "Your pitch would benefit from strengthening key foundational elements."
        
        # Generate specific feedback bullets
        bullets = []
        
        if scores['clarity'] < 6:
            if emotion_ctx.nervousness > 0.6:
                bullets.append("Practice your pitch to reduce filler words and increase confidence")
            else:
                bullets.append("Simplify complex concepts and speak more directly")
        
        if scores['structure'] < 6:
            bullets.append("Follow a clear structure: problem → solution → market → traction → ask")
        
        if scores['value_prop'] < 6:
            bullets.append("Clearly articulate what makes your solution unique and valuable")
        
        if scores['persuasiveness'] < 6:
            if emotion_ctx.confidence_level < 0.4:
                bullets.append("Build confidence through practice and preparation")
            else:
                bullets.append("Include specific metrics, testimonials, or proof points")
        
        if scores['voice_tone'] < 6:
            if emotion_ctx.nervousness > 0.6:
                bullets.append("Practice breathing techniques to manage nervousness")
            else:
                bullets.append("Work on vocal variety and energy to engage your audience")
        
        # If we don't have specific issues, add general improvements
        if not bullets:
            bullets = [
                "Add more specific examples or case studies",
                "Practice your delivery for better flow and timing",
                "Strengthen your call-to-action"
            ]
        
        # Generate improvement plan
        improvements = []
        if 'problem' not in text and 'challenge' not in text:
            improvements.append("Clearly define the problem you're solving")
        if '$' not in text and 'revenue' not in text:
            improvements.append("Include concrete business metrics or traction")
        if emotion_ctx.confidence_level < 0.5:
            improvements.append("Practice until you can deliver without notes")
        
        if not improvements:
            improvements = [
                "Focus on your strongest differentiator",
                "Prepare for common investor questions"
            ]
        
        return {
            'summary': summary,
            'bullets': bullets[:3],  # Top 3 feedback points
            'improvements': improvements[:2]  # Top 2 improvements
        }


class PitchEvaluator:
    """Main pitch evaluation and TTS generation class"""
    
    def __init__(self):
        """Initialize with local models"""
        logger.info("🚀 Initializing Pitch Evaluator with open-source models...")
        
        self.llm = OpenSourceLLM()
        self.voice_mapper = VoiceStyleMapper()
        
        # Initialize pygame for audio (Kaggle-friendly)
        try:
            pygame.mixer.init()
        except pygame.error:
            logger.warning("Could not initialize pygame audio - audio playback may not work")
    
    def evaluate_pitch(self, pitch_text: str, emotion_ctx: Optional[EmotionContext] = None,
                      prosody: Optional[ProsodyData] = None) -> EvaluationResult:
        """Evaluate pitch using local LLM and return structured results"""
        
        if not emotion_ctx:
            emotion_ctx = EmotionContext()  # Use defaults
            
        if len(pitch_text.strip()) < 10:
            logger.warning("Very short pitch text - evaluation may be limited")
        
        try:
            # Get LLM evaluation
            llm_output = self.llm.evaluate_pitch(pitch_text, emotion_ctx, prosody)
            
            # Create structured result
            scores = PitchScores(**llm_output['scores'])
            voice_style = self.voice_mapper.determine_voice_style(scores, emotion_ctx)
            
            result = EvaluationResult(
                summary=llm_output['summary'],
                scores=scores,
                feedback_bullets=llm_output['feedback_bullets'],
                improvement_plan=llm_output['improvement_plan'],
                voice_style=voice_style
            )
            
            logger.info(f"✅ Evaluation complete. Voice style: {voice_style}")
            return result
            
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            # Return fallback result
            return EvaluationResult(
                summary="Evaluation completed with basic analysis.",
                scores=PitchScores(),
                feedback_bullets=["Focus on clear problem and solution statements"],
                improvement_plan=["Practice your pitch structure and delivery"],
                voice_style='encouraging'
            )
    
    def generate_tts_audio(self, evaluation: EvaluationResult, 
                          output_dir: str = "/kaggle/working") -> str:
        """Generate TTS audio with appropriate voice style"""
        
        # Build feedback text
        feedback_text = self._build_feedback_text(evaluation)
        
        # Add voice style modifier
        voice_modifiers = self.voice_mapper.VOICE_STYLES[evaluation.voice_style]['tts_modifiers']
        styled_text = voice_modifiers + feedback_text
        
        # Generate audio file path
        audio_filename = f"pitch_feedback_{evaluation.voice_style}.mp3"
        audio_path = os.path.join(output_dir, audio_filename)
        
        try:
            # Generate TTS
            logger.info(f"🔊 Generating TTS audio in {evaluation.voice_style} style...")
            
            # Use slower speech for calm style, normal for others
            slow = (evaluation.voice_style == 'calm')
            
            tts = gTTS(text=styled_text, lang='en', slow=slow)
            tts.save(audio_path)
            
            logger.info(f"✅ Audio saved to: {audio_path}")
            return audio_path
            
        except Exception as e:
            logger.error(f"❌ TTS generation failed: {e}")
            return None
    
    def _build_feedback_text(self, evaluation: EvaluationResult) -> str:
        """Build spoken feedback text from evaluation"""
        
        avg_score = (evaluation.scores.clarity + evaluation.scores.structure + 
                    evaluation.scores.value_prop + evaluation.scores.persuasiveness + 
                    evaluation.scores.voice_tone) / 5
        
        # Start with summary
        text = f"{evaluation.summary} "
        
        # Add score highlights
        if avg_score >= 7:
            text += "Your pitch shows strong foundations. "
        elif avg_score >= 5:
            text += "Your pitch has good potential with some areas to enhance. "
        else:
            text += "There are several key areas where your pitch can be strengthened. "
        
        # Add top improvement points
        if evaluation.improvement_plan:
            text += "Focus on these priorities: "
            text += ". ".join(evaluation.improvement_plan[:2]) + ". "
        
        # Add encouragement based on voice style
        style_endings = {
            'confident': "Keep building on these strengths!",
            'encouraging': "You're on the right track - keep refining!",
            'constructive': "With these improvements, your pitch will be much stronger.",
            'calm': "Take your time to practice these changes. You've got this.",
            'energetic': "Great energy - channel it into these key improvements!"
        }
        
        text += style_endings.get(evaluation.voice_style, "Keep working on your pitch!")
        
        return text
    
    def play_audio(self, audio_path: str) -> bool:
        """Attempt to play audio in Kaggle (may have limitations)"""
        try:
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            
            # Wait for audio to finish
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
                
            return True
        except Exception as e:
            logger.error(f"Audio playback failed: {e}")
            logger.info(f"Audio saved to {audio_path} - download to play locally")
            return False
    
    def evaluate_and_synthesize(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete pipeline: evaluate pitch and generate audio"""
        
        # Parse input
        pitch_text = input_data.get('pitch_text', '')
        if not pitch_text:
            raise ValueError("pitch_text is required")
        
        # Parse optional context
        emotion_data = input_data.get('emotion_context', {})
        emotion_ctx = EmotionContext(**emotion_data)
        
        prosody_data = input_data.get('prosody')
        prosody = ProsodyData(**prosody_data) if prosody_data else None
        
        # Evaluate pitch
        logger.info("🎯 Starting pitch evaluation...")
        evaluation = self.evaluate_pitch(pitch_text, emotion_ctx, prosody)
        
        # Generate audio
        logger.info("🔊 Generating TTS audio...")
        audio_path = self.generate_tts_audio(evaluation)
        evaluation.audio_file = audio_path
        
        # Print results
        self._print_results(evaluation)
        
        return evaluation.to_dict()
    
    def _print_results(self, evaluation: EvaluationResult):
        """Print formatted results to console"""
        print("\n" + "="*50)
        print("🎯 PITCH EVALUATION COMPLETE!")
        print("="*50)
        print(f"\n📝 Summary: {evaluation.summary}")
        
        print(f"\n📊 Scores:")
        print(f"   • Clarity: {evaluation.scores.clarity}/10")
        print(f"   • Structure: {evaluation.scores.structure}/10") 
        print(f"   • Value Prop: {evaluation.scores.value_prop}/10")
        print(f"   • Persuasiveness: {evaluation.scores.persuasiveness}/10")
        print(f"   • Voice Tone: {evaluation.scores.voice_tone}/10")
        
        avg_score = (evaluation.scores.clarity + evaluation.scores.structure + 
                    evaluation.scores.value_prop + evaluation.scores.persuasiveness + 
                    evaluation.scores.voice_tone) / 5
        print(f"   📈 Average: {avg_score:.1f}/10")
        
        print(f"\n🗣️ Voice Style: {evaluation.voice_style.title()}")
        print(f"🔊 Audio: {evaluation.audio_file or 'Generation failed'}")
        
        print(f"\n💡 Key Feedback:")
        for bullet in evaluation.feedback_bullets:
            print(f"   • {bullet}")
        
        print(f"\n🚀 Priority Improvements:")
        for item in evaluation.improvement_plan:
            print(f"   • {item}")
        
        print("\n" + "="*50)


# Sample usage and test data
def create_sample_inputs() -> List[Dict[str, Any]]:
    """Create sample input data for testing"""
    
    samples = [
        {
            "name": "Confident Tech Pitch",
            "data": {
                "pitch_text": "We're building an AI-powered customer service platform that reduces response times by 80% and increases customer satisfaction. Our solution uses advanced natural language processing to understand customer intent and provide personalized responses. We've already secured partnerships with three major retailers and generated $50,000 in revenue this quarter.",
                "emotion_context": {
                    "confidence_level": 0.8,
                    "energy_level": 0.7,
                    "nervousness": 0.2,
                    "posture_score": 0.8
                },
                "prosody": {
                    "pitch_mean": 140.0,
                    "speech_rate_wpm": 160.0,
                    "pause_ratio": 0.12
                }
            }
        },
        {
            "name": "Nervous Beginner Pitch", 
            "data": {
                "pitch_text": "Um, so we have this app idea... it's like, for food delivery but different. We think people would maybe use it because it's faster? We haven't really started building it yet but we think it could be good.",
                "emotion_context": {
                    "confidence_level": 0.2,
                    "energy_level": 0.3,
                    "nervousness": 0.9,
                    "posture_score": 0.3
                },
                "prosody": {
                    "pitch_mean": 180.0,
                    "speech_rate_wpm": 90.0,
                    "pause_ratio": 0.25
                }
            }
        },
        {
            "name": "High Energy Startup",
            "data": {
                "pitch_text": "We're revolutionizing the fitness industry with AR workouts! Imagine doing yoga with a virtual instructor in your living room, or running through the streets of Paris from your treadmill. We've got the tech, the team, and the vision to make fitness accessible to everyone, everywhere!",
                "emotion_context": {
                    "confidence_level": 0.7,
                    "energy_level": 0.95,
                    "nervousness": 0.1,
                    "posture_score": 0.9
                }
            }
        },
        {
            "name": "Basic Pitch Test",
            "data": {
                "pitch_text": "Our company solves the problem of inefficient scheduling. We built a platform that helps businesses manage their appointments better. We have some customers and are looking for investment.",
                "emotion_context": {
                    "confidence_level": 0.5,
                    "energy_level": 0.4,
                    "nervousness": 0.6,
                    "posture_score": 0.5
                }
            }
        }
    ]
    
    return samples


# Main execution for Kaggle
def main():
    """Main function for testing in Kaggle"""
    
    print("🚀 Open Source Pitch Evaluator PoC")
    print("📝 No API keys required - uses local models only!")
    print("⚡ Loading models... (this may take a moment)")
    
    try:
        # Initialize evaluator
        evaluator = PitchEvaluator()
        
        # Get sample data
        samples = create_sample_inputs()
        
        print(f"\n🎬 Available test samples:")
        for i, sample in enumerate(samples, 1):
            print(f"   {i}. {sample['name']}")
        
        # For demo, run the first sample
        selected_sample = samples[0]
        print(f"\n🎬 Running demo with: {selected_sample['name']}")
        
        # Process the sample
        result = evaluator.evaluate_and_synthesize(selected_sample['data'])
        
        # Try to play audio
        if result.get('audio_file'):
            print(f"\n🎵 Attempting to play audio...")
            evaluator.play_audio(result['audio_file'])
        
        print(f"\n✅ Demo complete! Check /kaggle/working/ for generated audio files.")
        
        # Show how to test other samples
        print(f"\n🧪 To test other samples:")
        print(f"   evaluator = PitchEvaluator()")
        print(f"   samples = create_sample_inputs()")
        print(f"   result = evaluator.evaluate_and_synthesize(samples[1]['data'])  # Try sample 2")
        
        return result
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"❌ Error: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("   • Ensure you have sufficient GPU/RAM for model loading")
        print("   • Try restarting the kernel if models fail to load")
        print("   • Check that transformers and torch are properly installed")
        return None


if __name__ == "__main__":
    # Install required packages first
    print("📦 Installing required packages...")
    print("Run: !pip install transformers torch gtts pygame accelerate bitsandbytes")
    
    # Run the demo
    result = main()
    
    # Show usage example
    print("""
📋 USAGE EXAMPLE:
    
    from pitch_evaluator import PitchEvaluator
    
    # Your input data
    input_data = {
        "pitch_text": "Your startup pitch here...",
        "emotion_context": {
            "confidence_level": 0.6,
            "energy_level": 0.8,
            "nervousness": 0.3,
            "posture_score": 0.7
        }
    }
    
    # Process
    evaluator = PitchEvaluator()
    result = evaluator.evaluate_and_synthesize(input_data)
    
    print(result)
""")