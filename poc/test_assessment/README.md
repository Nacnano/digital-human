# digital-human

A proof-of-concept repository implementing the middle part of a "digital human" pitch evaluation pipeline: LLM-based pitch analysis and TTS-based spoken feedback.

The full system (planned) has three large domains: input capture (audio + video → features and text), analysis (LLM + specialty models), and rendering (digital human avatar + emotional audio). This repo implements a compact PoC that simulates or accepts SST text, runs an LLM evaluation, and produces audio feedback.

## Goals of this PoC

- Provide a reproducible pipeline for evaluating pitch text and producing spoken feedback.
- Demonstrate how to incorporate voice-tone signals into the LLM evaluation and how to map evaluation output to TTS prosody.
- Ship a minimal runnable example you can extend to include real SST, emotion, and pose models.

## Project layout

- `pitch_evaluator.py` — main PoC module. Evaluates pitch text with an LLM and generates TTS feedback.
- `requirements.txt` — Python dependencies for the PoC.
- `.env.example` — example environment file for API keys.

## High-level architecture

Attachment: refer to the supplied workflow diagram for a visual overview (Audio/video → SST / Pose classifier → LLM → Model2/Model3 / TTS)

This repo focuses on the central path:

1.  SST (Speech-to-Text) — external to this PoC; produces: pitch_text, optional prosody metadata (pitch, energy, speaking_rate, pauses).
2.  LLM evaluation — consumes pitch_text + optional prosody metadata and returns structured feedback.
3.  TTS generation — converts the feedback into spoken audio; optionally accepts prosody hints to alter voice tone.

## Detailed workflows and contracts

Below are the concrete contracts and data shapes for each stage so integrations are explicit.

1.  Speech-to-Text (input contract)

- Inputs: raw audio file (wav/ogg/mp3)
- Outputs (JSON):
  - `pitch_text` (string): the transcribed speech
  - `prosody` (optional object): {`pitch_mean`: float, `pitch_std`: float, `energy_mean`: float, `speech_rate_wpm`: float, `pause_ratio`: float}
  - `timestamps` (optional): word/time alignments

2.  LLM Evaluation (contract implemented in PoC)

- Inputs:
  - `pitch_text` (required)
  - `prosody` (optional)
  - `context` (optional): product/domain/company facts
- Output (JSON-ish text or structured object):
  - `summary` (short summary, 1–2 sentences)
  - `scores` (object): {clarity:0-10, structure:0-10, value_prop:0-10, persuasiveness:0-10, voice_tone:0-10}
  - `bullets` (array): actionable feedback points
  - `improvement_plan` (short list of suggestions)

Implementation notes (PoC):

- The prompt used in `pitch_evaluator.py` asks the LLM to evaluate clarity, structure, value, persuasiveness, areas for improvement, and voice tone/emotion. If `prosody` metadata is present, include it in the prompt so the LLM can reason from it.

Prompt sketch (PoC):

- System: expert pitch evaluator
- User: Provide the pitch text plus optional prosody summary, then ask for a structured evaluation (summary, numeric scores, bullets, improvement plan) and an example phrase to speak with an improved tone.

3.  TTS Generation (contract)

- Inputs: `feedback_text` (string), optional `voice_style` or `ssml_hints` (to encode prosody)
- Outputs: `audio_file` (mp3/wav) and `playback` success/failure

PoC options and voice-tone handling:

- gTTS (used in PoC): simple, free, limited control over prosody. Good for quick demos.
- SSML-capable providers (Google Cloud TTS, Amazon Polly, Azure): allow fine-grained prosody and voice selection. For production, prefer these if you need expressive tone mapping.

Voice-tone mapping strategy (how to convert evaluation → audio tone):

- Map `voice_tone` score and LLM-kept tone suggestion to a small set of voice styles: {neutral, confident, warm, emphatic}.
- For SSML-capable engines: apply `prosody` tags (rate, pitch, volume) and emphasis on key phrases.
- For gTTS: preface the output with short textual cues ("In a confident tone: ...") or choose different languages/variants where available; it's limited.

## Edge cases and error modes

- Missing SST prosody: LLM falls back to text-only evaluation and marks voice-tone confidence as low.
- Very short pitches (< 10 words): return a warning and suggest elaboration.
- Unreliable TTS playback: save to disk and offer playback instructions instead of streaming.
- LLM rate limits / API errors: implement exponential backoff and clear error messages.

## How to run the PoC (Windows PowerShell)

1.  Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\activate
```

2.  Install dependencies:

```powershell
pip install -r requirements.txt
```

3.  Copy the environment template and add your OpenAI key:

```powershell
Copy-Item .env.example .env
# then edit .env and set OPENAI_API_KEY
```

4.  Run the PoC:

```powershell
python pitch_evaluator.py
```

The script currently uses a sample pitch text. Replace the sample or refactor the `main()` function to accept a JSON file that contains `pitch_text` and optional `prosody` metadata.

## Tests and quality gates (recommended)

- Unit test idea: call `evaluate_pitch()` with a known short pitch and assert returned text contains keys like "Improvement" or score numbers.
- Linting: ensure dependencies installed and linter clean (fix openai typing warnings as needed).

## Next steps and extensions

- Integrate a real Speech-to-Text engine (OpenAI Whisper, Vosk, or cloud STT) to supply `pitch_text` and prosody metadata.
- Replace gTTS with an SSML-capable TTS for expressive voice rendering (Google Cloud TTS, Polly, Azure).
- Add an emotion classifier (audio or video-based) and feed results as `context` to the LLM.
- Create an API wrapper (Flask/FastAPI) and a simple web UI to upload audio and receive playback.

## Files changed in this PoC

- `pitch_evaluator.py` — LLM prompt and TTS demo implementation
- `requirements.txt` — packages needed to run the demo
- `.env.example` — OpenAI key placeholder

## Contact / notes

This README focuses on the evaluation + TTS middle layer and documents explicit data shapes and contracts so you can wire upstream SST and downstream avatar rendering. If you'd like, I can:

- Add a small SST integration using Whisper (local) or a cloud STT, or
- Swap gTTS for an SSML-capable TTS and demonstrate mapping evaluation→SSML for a confident/empathetic voice.

Pick one and I'll implement it next.
