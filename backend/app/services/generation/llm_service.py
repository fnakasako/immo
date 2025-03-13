"""
LLM Service Module

This module provides a service for interacting with LLMs (Large Language Models).
It abstracts the details of the LLM API and provides a clean interface for generation.
"""
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import anthropic

from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMServiceException(Exception):
    """Custom exception for LLM service errors"""
    pass

class ContentModerationException(LLMServiceException):
    """Raised when content violates moderation policies"""
    pass

class LLMService:
    """Service for interacting with LLM APIs"""
    
    def __init__(self, api_key: str = None, model: str = "claude-3-sonnet-20240229"):
        """Initialize with API key and model"""
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        
        # Log the first few characters of the API key for debugging
        if self.api_key:
            logger.info(f"Initializing LLMService with API key starting with: {self.api_key[:10]}...")
            logger.info(f"API key length: {len(self.api_key)}")
            # Check if the API key format is valid
            if not self.api_key.startswith("sk-ant-"):
                logger.error("API key does not have the expected format (should start with 'sk-ant-')")
        else:
            logger.error("No API key provided to LLMService")
            
        # Initialize the Anthropic client
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
        self.model = model
        self.max_retries = 3
        self.temperature_outline = 0.7  # More creative for outlines
        self.temperature_scenes = 0.75  # Balanced for scene planning
        self.temperature_prose = 0.8    # Most creative for prose
        self.timeout = 120  # Seconds
        
        # Verify API key on initialization
        asyncio.create_task(self._verify_api_key())
    
    async def _verify_api_key(self):
        """Verify that the API key is valid by making a simple request to the Anthropic API"""
        try:
            # Make a simple request to the Anthropic API to verify the API key
            logger.info("Verifying API key with Anthropic...")
            await self.client.messages.create(
                model=self.model,
                system="Test",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=10
            )
            logger.info("API key verification successful")
        except anthropic.AuthenticationError as e:
            logger.error(f"API key verification failed: {str(e)}")
            # Don't raise an exception here, just log the error
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=30),
        retry=retry_if_exception_type(
            (anthropic.APITimeoutError, anthropic.APIConnectionError, anthropic.RateLimitError)
        )
    )
    async def generate_text(self, prompt: str, system_prompt: str = "You are a professional content creator.", 
                           temperature: float = None, max_tokens: int = 4000) -> str:
        """
        Generate text from the LLM
        
        Args:
            prompt: The prompt to send to the model
            system_prompt: The system prompt to use
            temperature: Temperature for generation (defaults to outline temperature)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        try:
            # Use default temperature if not specified
            if temperature is None:
                temperature = self.temperature_outline
                
            logger.info(f"Generating text with prompt: {prompt[:100]}...")
            
            response = await self.client.messages.create(
                model=self.model,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            generated_text = response.content[0].text
            logger.info(f"Successfully generated text ({len(generated_text)} chars)")
            return generated_text
            
        except anthropic.AuthenticationError as e:
            logger.error(f"Authentication error in generate_text: {str(e)}")
            raise LLMServiceException("Authentication failed: Invalid API key or credentials")
        except Exception as e:
            logger.error(f"Unexpected error in generate_text: {str(e)}")
            raise LLMServiceException(f"Failed to generate text: {str(e)}")
    
    async def stream_generation(self, prompt: str, system_prompt: str = "You are a professional content creator.", 
                               temperature: float = None, max_tokens: int = 4000) -> AsyncGenerator[str, None]:
        """
        Stream generation results from the LLM
        
        Args:
            prompt: The prompt to send to the model
            system_prompt: The system prompt to use
            temperature: Temperature for generation (defaults to prose temperature)
            max_tokens: Maximum tokens to generate
            
        Yields:
            Chunks of generated text as they become available
        """
        try:
            # Use default temperature if not specified
            if temperature is None:
                temperature = self.temperature_prose
                
            logger.info(f"Starting streaming generation with prompt: {prompt[:100]}...")
            
            async with anthropic.AsyncStream(
                client=self.client,
                model=self.model,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            ) as stream:
                async for chunk in stream:
                    if chunk.delta.text:
                        yield chunk.delta.text
                        
            logger.info("Streaming generation completed")
            
        except anthropic.AuthenticationError as e:
            logger.error(f"Authentication error in stream_generation: {str(e)}")
            raise LLMServiceException("Authentication failed: Invalid API key or credentials")
        except Exception as e:
            logger.error(f"Error in stream_generation: {str(e)}")
            raise LLMServiceException(f"Failed to stream generation: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=30),
        retry=retry_if_exception_type(
            (anthropic.APITimeoutError, anthropic.APIConnectionError, anthropic.RateLimitError)
        )
    )
    async def generate_json(self, prompt: str, system_prompt: str = "You are a professional content creator.", 
                           temperature: float = None, max_tokens: int = 4000) -> Dict[str, Any]:
        """
        Generate JSON from the LLM
        
        Args:
            prompt: The prompt to send to the model
            system_prompt: The system prompt to use
            temperature: Temperature for generation (defaults to outline temperature)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated JSON as a dictionary
        """
        try:
            # Generate text
            text = await self.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Parse JSON
            try:
                return json.loads(text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                logger.error(f"Response text: {text}")
                raise LLMServiceException(f"Invalid JSON response: {str(e)}")
            
        except Exception as e:
            if isinstance(e, LLMServiceException):
                raise
            logger.error(f"Unexpected error in generate_json: {str(e)}")
            raise LLMServiceException(f"Failed to generate JSON: {str(e)}")
    
    async def stream_json(self, prompt: str, system_prompt: str = "You are a professional content creator.", 
                         temperature: float = None, max_tokens: int = 4000) -> AsyncGenerator[str, None]:
        """
        Stream JSON generation from the LLM
        
        Args:
            prompt: The prompt to send to the model
            system_prompt: The system prompt to use
            temperature: Temperature for generation (defaults to outline temperature)
            max_tokens: Maximum tokens to generate
            
        Yields:
            Chunks of the generated JSON as they become available
        """
        # This is just a wrapper around stream_generation
        # The caller will need to accumulate the chunks and parse the JSON
        async for chunk in self.stream_generation(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature or self.temperature_outline,
            max_tokens=max_tokens
        ):
            yield chunk
