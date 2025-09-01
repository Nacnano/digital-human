from pathlib import Path
import openai
from gtts import gTTS
import soundfile as sf
import sounddevice as sd
from decouple import config

# Configure OpenAI API
openai.api_key = config('OPENAI_API_KEY')

class PitchEvaluator:
    def __init__(self):
        self.evaluation_prompt = """
        You are an expert pitch evaluator. Analyze the following pitch and provide detailed feedback on:
        1. Clarity and Structure
        2. Value Proposition
        3. Persuasiveness
        4. Areas for Improvement
        5. Voice Tone and Emotion: Analyze the vocal tone, intonation, and emotional cues that can be inferred from the pitch.

        Format your response in a clear, constructive manner.

        Pitch to evaluate:
        {pitch_text}
        """

    def evaluate_pitch(self, pitch_text):
        """Evaluate the pitch using GPT model, with fallback if ChatCompletion not available"""
        try:
            # Try using chat completion
            response = openai.ChatCompletion.create(  # type: ignore
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert pitch evaluator providing constructive feedback."},
                    {"role": "user", "content": self.evaluation_prompt.format(pitch_text=pitch_text)}
                ]
            )
            return response.choices[0].message.content
        except AttributeError:
            # Fallback to text completion if ChatCompletion is not available
            prompt = self.evaluation_prompt.format(pitch_text=pitch_text)
            response = openai.Completion.create(  # type: ignore
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=500
            )
            return response.choices[0].text.strip()
        except Exception as e:
            return f"Error during evaluation: {str(e)}"

    def generate_feedback_audio(self, feedback_text, output_file="feedback.mp3"):
        """
        Convert feedback text to speech using gTTS
        """
        try:
            tts = gTTS(text=feedback_text, lang='en')
            tts.save(output_file)
            return output_file
        except Exception as e:
            return f"Error generating audio: {str(e)}"

    def play_audio(self, file_path):
        """
        Play the generated audio feedback
        """
        try:
            data, samplerate = sf.read(file_path)
            sd.play(data, samplerate)
            sd.wait()  # Wait until the audio is finished playing
        except Exception as e:
            print(f"Error playing audio: {str(e)}")

def main():
    # Example pitch text (in a real application, this would come from SST)
    sample_pitch = """
    Hello, I'm presenting a revolutionary app that helps people learn languages faster.
    Our app uses AI to create personalized learning paths and adapts to each user's progress.
    We've already gained 10,000 users in our beta phase and seen an average learning speed
    improvement of 40% compared to traditional methods.
    """

    # Create evaluator instance
    evaluator = PitchEvaluator()

    # Get evaluation
    print("Evaluating pitch...")
    feedback = evaluator.evaluate_pitch(sample_pitch)
    print("\nFeedback:")
    print(feedback)

    # Generate and play audio feedback
    print("\nGenerating audio feedback...")
    audio_file = evaluator.generate_feedback_audio(feedback)
    print(f"Audio saved as: {audio_file}")
    print("Playing audio feedback...")
    evaluator.play_audio(audio_file)

if __name__ == "__main__":
    main()
