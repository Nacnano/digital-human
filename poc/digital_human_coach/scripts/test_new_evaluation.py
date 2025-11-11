"""
Test script for new evaluation format
"""
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.backend.models.schemas import (
    ScoreWithComment, SpeechEvaluation, PoseEvaluation, EvaluationFeedback
)


def test_parse_evaluation():
    """Test parsing the new evaluation format"""
    
    # Sample response from LLM
    sample_json = """
    {
      "Speech": {
        "Speed": { "score": 2, "comment": "Moderate pace, easy to follow." },
        "Naturalness": { "score": 3, "comment": "Very conversational and confident." },
        "Continuity": { "score": 2, "comment": "Generally smooth with slight hesitations." },
        "ListeningEffort": { "score": 4, "comment": "Mostly effortless, minor moments needing focus." }
      },
      "Pose": {
        "EyeContact": { "score": 2, "comment": "Covers most of audience but checks notes often." },
        "Posture": { "score": 3, "comment": "Confident stance with purposeful movement." },
        "HandGestures": { "score": 2, "comment": "Some effective gestures but not very varied." }
      },
      "OverallFeedback": "Strong presentation with natural speech and confident posture. Improving eye contact and gesture variety could further enhance engagement."
    }
    """
    
    print("Testing new evaluation format parsing...\n")
    
    try:
        # Parse JSON
        data = json.loads(sample_json)
        print("✅ JSON parsed successfully")
        
        # Create Pydantic models
        feedback = EvaluationFeedback(
            Speech=SpeechEvaluation(
                Speed=ScoreWithComment(**data["Speech"]["Speed"]),
                Naturalness=ScoreWithComment(**data["Speech"]["Naturalness"]),
                Continuity=ScoreWithComment(**data["Speech"]["Continuity"]),
                ListeningEffort=ScoreWithComment(**data["Speech"]["ListeningEffort"])
            ),
            Pose=PoseEvaluation(
                EyeContact=ScoreWithComment(**data["Pose"]["EyeContact"]),
                Posture=ScoreWithComment(**data["Pose"]["Posture"]),
                HandGestures=ScoreWithComment(**data["Pose"]["HandGestures"])
            ),
            OverallFeedback=data["OverallFeedback"]
        )
        
        print("✅ Pydantic models created successfully\n")
        
        # Display results
        print("=" * 60)
        print("EVALUATION RESULTS")
        print("=" * 60)
        
        print("\n📊 SPEECH EVALUATION:")
        print(f"  Speed ({feedback.Speech.Speed.score}/3): {feedback.Speech.Speed.comment}")
        print(f"  Naturalness ({feedback.Speech.Naturalness.score}/3): {feedback.Speech.Naturalness.comment}")
        print(f"  Continuity ({feedback.Speech.Continuity.score}/3): {feedback.Speech.Continuity.comment}")
        print(f"  Listening Effort ({feedback.Speech.ListeningEffort.score}/5): {feedback.Speech.ListeningEffort.comment}")
        
        print("\n🧍 POSE EVALUATION:")
        print(f"  Eye Contact ({feedback.Pose.EyeContact.score}/3): {feedback.Pose.EyeContact.comment}")
        print(f"  Posture ({feedback.Pose.Posture.score}/3): {feedback.Pose.Posture.comment}")
        print(f"  Hand Gestures ({feedback.Pose.HandGestures.score}/3): {feedback.Pose.HandGestures.comment}")
        
        print(f"\n💬 OVERALL FEEDBACK:")
        print(f"  {feedback.OverallFeedback}")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
        # Test JSON serialization
        print("\nTesting JSON serialization...")
        json_output = feedback.model_dump(mode="json")
        print("✅ JSON serialization successful")
        print(f"\nSerialized output:\n{json.dumps(json_output, indent=2)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fallback():
    """Test fallback behavior when parsing fails"""
    print("\n" + "=" * 60)
    print("TESTING FALLBACK BEHAVIOR")
    print("=" * 60 + "\n")
    
    try:
        # Create fallback feedback
        fallback = EvaluationFeedback(
            Speech=SpeechEvaluation(
                Speed=ScoreWithComment(score=2, comment="Moderate pace observed."),
                Naturalness=ScoreWithComment(score=2, comment="Somewhat natural delivery."),
                Continuity=ScoreWithComment(score=2, comment="Generally smooth flow."),
                ListeningEffort=ScoreWithComment(score=3, comment="Moderate listening effort.")
            ),
            Pose=PoseEvaluation(
                EyeContact=ScoreWithComment(score=2, comment="Good eye contact maintained."),
                Posture=ScoreWithComment(score=2, comment="Good posture overall."),
                HandGestures=ScoreWithComment(score=2, comment="Some effective gestures used.")
            ),
            OverallFeedback="Evaluation completed with default scores."
        )
        
        print("✅ Fallback structure created successfully")
        print(f"\nFallback overall feedback: {fallback.OverallFeedback}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fallback creation failed: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("NEW EVALUATION FORMAT TEST SUITE")
    print("=" * 60 + "\n")
    
    test1 = test_parse_evaluation()
    test2 = test_fallback()
    
    print("\n" + "=" * 60)
    if test1 and test2:
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nThe new evaluation format is working correctly!")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        sys.exit(1)
