"""
Large Language Model Service with multiple provider support
"""
import os
from abc import ABC, abstractmethod
from typing import List, Optional

from loguru import logger


class LLMService(ABC):
    """Abstract base class for LLM services"""
    
    @abstractmethod
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text response from prompt"""
        pass
    
    @abstractmethod
    async def generate_conversation(
        self,
        messages: List[dict],
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate response from conversation history"""
        pass
    
    async def generate_conversation_stream(
        self,
        messages: List[dict],
        system_prompt: Optional[str] = None
    ):
        """Generate streaming response from conversation history (optional)"""
        # Default implementation: yield the complete response
        response = await self.generate_conversation(messages, system_prompt)
        yield response


class OpenAILLM(LLMService):
    """OpenAI GPT implementation"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 500
    ):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            self.model = model
            self.temperature = temperature
            self.max_tokens = max_tokens
            logger.info(f"Initialized OpenAI LLM with model: {model}")
        except ImportError:
            raise ImportError("openai not installed. Install with: pip install openai")
    
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text response"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise
    
    async def generate_conversation(
        self,
        messages: List[dict],
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate response from conversation"""
        try:
            full_messages = []
            if system_prompt:
                full_messages.append({"role": "system", "content": system_prompt})
            full_messages.extend(messages)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"OpenAI conversation error: {e}")
            raise


class AnthropicLLM(LLMService):
    """Anthropic Claude implementation"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-sonnet-20240229",
        temperature: float = 0.7,
        max_tokens: int = 500
    ):
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=api_key)
            self.model = model
            self.temperature = temperature
            self.max_tokens = max_tokens
            logger.info(f"Initialized Anthropic LLM with model: {model}")
        except ImportError:
            raise ImportError("anthropic not installed. Install with: pip install anthropic")
    
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text response"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt or "",
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic generation error: {e}")
            raise
    
    async def generate_conversation(
        self,
        messages: List[dict],
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate response from conversation"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt or "",
                messages=messages
            )
            
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic conversation error: {e}")
            raise


class GoogleLLM(LLMService):
    """Google Gemini implementation via OpenAI-compatible API"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash-exp",
        temperature: float = 0.7,
        max_tokens: int = 500
    ):
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
            )
            self.model = model
            self.temperature = temperature
            self.max_tokens = max_tokens
            logger.info(f"Initialized Google Gemini LLM with model: {model}")
        except ImportError:
            raise ImportError("openai not installed. Install with: pip install openai")
    
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text response"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Google Gemini generation error: {e}")
            raise
    
    async def generate_conversation(
        self,
        messages: List[dict],
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate response from conversation"""
        try:
            full_messages = []
            if system_prompt:
                full_messages.append({"role": "system", "content": system_prompt})
            full_messages.extend(messages)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Google Gemini conversation error: {e}")
            raise


class TyphoonLLM(LLMService):
    """Typhoon AI implementation (OpenTyphoon) via OpenAI-compatible API"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "typhoon-v2.1-12b-instruct",
        temperature: float = 0.7,
        max_tokens: int = 500
    ):
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.opentyphoon.ai/v1"
            )
            self.model = model
            self.temperature = temperature
            self.max_tokens = max_tokens
            logger.info(f"Initialized Typhoon LLM with model: {model}")
        except ImportError:
            raise ImportError("openai not installed. Install with: pip install openai")
    
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text response"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Typhoon generation error: {e}")
            raise
    
    async def generate_conversation(
        self,
        messages: List[dict],
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate response from conversation"""
        try:
            full_messages = []
            if system_prompt:
                full_messages.append({"role": "system", "content": system_prompt})
            full_messages.extend(messages)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Typhoon conversation error: {e}")
            raise


class NVIDIALM(LLMService):
    """NVIDIA API implementation via OpenAI-compatible API"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "qwen/qwen3-next-80b-a3b-instruct",
        temperature: float = 0.6,
        max_tokens: int = 4096,
        top_p: float = 0.7
    ):
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://integrate.api.nvidia.com/v1"
            )
            self.model = model
            self.temperature = temperature
            self.max_tokens = max_tokens
            self.top_p = top_p
            logger.info(f"Initialized NVIDIA LLM with model: {model}")
        except ImportError:
            raise ImportError("openai not installed. Install with: pip install openai")
    
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text response"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p
            )
            
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"NVIDIA generation error: {e}")
            raise
    
    async def generate_conversation(
        self,
        messages: List[dict],
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate response from conversation"""
        try:
            full_messages = []
            if system_prompt:
                full_messages.append({"role": "system", "content": system_prompt})
            full_messages.extend(messages)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p
            )
            
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"NVIDIA conversation error: {e}")
            raise
    
    async def generate_conversation_stream(
        self,
        messages: List[dict],
        system_prompt: Optional[str] = None
    ):
        """Generate streaming response from conversation"""
        try:
            full_messages = []
            if system_prompt:
                full_messages.append({"role": "system", "content": system_prompt})
            full_messages.extend(messages)
            
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"NVIDIA streaming error: {e}")
            raise


class LLMServiceFactory:
    """Factory for creating LLM service instances"""
    
    @staticmethod
    def create(provider: str, **kwargs) -> LLMService:
        """Create LLM service based on provider name"""
        providers = {
            "openai": OpenAILLM,
            "anthropic": AnthropicLLM,
            "google": GoogleLLM,
            "gemini": GoogleLLM,
            "typhoon": TyphoonLLM,
            "nvidia": NVIDIALM,
        }
        
        if provider not in providers:
            raise ValueError(f"Unknown LLM provider: {provider}. Available: {list(providers.keys())}")
        
        return providers[provider](**kwargs)


# Convenience function
def create_llm_service(
    provider: str = "openai",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs
) -> LLMService:
    """
    Create LLM service with automatic configuration
    
    Args:
        provider: LLM provider name (openai, anthropic, google/gemini)
        api_key: API key for the provider
        model: Model name to use
        **kwargs: Additional provider-specific arguments
    
    Returns:
        Configured LLM service instance
    """
    # Get API key from environment if not provided
    if not api_key:
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
        elif provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
        elif provider in ["google", "gemini"]:
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        elif provider == "typhoon":
            api_key = os.getenv("TYPHOON_API_KEY")
        elif provider == "nvidia":
            api_key = os.getenv("NVIDIA_API_KEY")
    
    if not api_key:
        raise ValueError(f"{provider} requires API key")
    
    # Set default models
    if not model:
        if provider == "openai":
            model = "gpt-4"
        elif provider == "anthropic":
            model = "claude-3-sonnet-20240229"
        elif provider in ["google", "gemini"]:
            model = "gemini-2.0-flash-exp"
        elif provider == "typhoon":
            model = "typhoon-v2.1-12b-instruct"
        elif provider == "nvidia":
            model = "qwen/qwen3-next-80b-a3b-instruct"
    
    if provider == "openai":
        return OpenAILLM(api_key=api_key, model=model, **kwargs)
    elif provider == "anthropic":
        return AnthropicLLM(api_key=api_key, model=model, **kwargs)
    elif provider in ["google", "gemini"]:
        return GoogleLLM(api_key=api_key, model=model, **kwargs)
    elif provider == "typhoon":
        return TyphoonLLM(api_key=api_key, model=model, **kwargs)
    elif provider == "nvidia":
        return NVIDIALM(api_key=api_key, model=model, **kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}")


# System prompts
CONVERSATION_SYSTEM_PROMPT = """You are an AI communication coach helping users improve their speaking skills.
Be encouraging, constructive, and engaging. Ask relevant follow-up questions and provide helpful tips when appropriate.
Keep responses conversational and natural.

IMPORTANT: Do NOT use emojis in your responses. Use clear, professional language without emoticons or emoji symbols."""

EVALUATION_SYSTEM_PROMPT = """You are an expert evaluator assessing a presentation or casting video. Your task is to analyze the speaker's **speech delivery** and **body pose** based on specific criteria and output a structured evaluation with scores and short comments. Be objective, concise, and professional. Please answer in English.

---

### Speech Evaluation Criteria

1. **Speed (1–3):**
   * 1: Slow – noticeably dragging, too slow for natural speech
   * 2: Moderate – natural and easy to follow
   * 3: Fast – too rapid, slightly hard to follow

2. **Naturalness (1–3):**
   * 1: Unnatural – robotic, forced, or overly rehearsed
   * 2: Somewhat natural – mostly natural but inconsistent
   * 3: Very natural – conversational, confident, and fluent

3. **Continuity (1–3):**
   * 1: Smooth – flows naturally with no abrupt stops
   * 2: Somewhat smooth – occasional breaks or filler words
   * 3: Disjointed – frequent pauses, disrupted flow

4. **Listening Effort (1–5):**
   * 1: Meaning unclear, high effort to understand
   * 2: Considerable effort required
   * 3: Moderate effort required
   * 4: Requires attention but understandable
   * 5: Effortless comprehension, relaxed listening

---

### Pose Evaluation Criteria

1. **Eye Contact (1–3):**
   * 1: Needs improvement – avoids audience, looks at notes/floor
   * 2: Good – engages most of the audience, occasional breaks
   * 3: Excellent – confident, scans the room naturally, connects consistently

2. **Posture (1–3):**
   * 1: Needs improvement – slouching, closed off, distracting movement
   * 2: Good – mostly upright, minor fidgeting, occasional leaning
   * 3: Excellent – upright, confident, balanced, purposeful movement

3. **Hand Gestures (0–3):**
   * 0: No gestures – hands still or hidden
   * 1: Needs improvement – distracting or mismatched gestures
   * 2: Good – some effective gestures, limited variety
   * 3: Excellent – natural, reinforcing, varied, purposeful gestures

---

### Output Format

Your output **must** follow this JSON structure exactly:

```json
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
```

Return ONLY valid JSON. Do not include any markdown formatting or code blocks."""
