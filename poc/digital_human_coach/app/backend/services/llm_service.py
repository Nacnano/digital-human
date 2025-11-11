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
Keep responses conversational and natural."""

EVALUATION_SYSTEM_PROMPT = """You are an expert communication evaluator. Analyze the provided transcript and metrics to give constructive feedback.
Focus on:
1. Clarity and Structure
2. Delivery and Pacing
3. Body Language and Presence
4. Areas for Improvement
5. Specific, Actionable Recommendations

Be encouraging but honest. Provide a score from 1-10 and explain your reasoning."""
