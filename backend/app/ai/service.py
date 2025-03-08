# app/ai/service.py
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import openai
from app.core.config import settings
from app.ai.prompts import PromptTemplates

logger = logging.getLogger(__name__)

class AIServiceException(Exception):
    """Custom exception for AI service errors"""
    pass

class ContentModerationException(AIServiceException):
    """Raised when content violates moderation policies"""
    pass

class AIService:
    """Service for generating content using AI"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4"):
        """Initialize with API key and model"""
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.client = openai.AsyncOpenAI(api_key=self.api_key)
        self.model = model
        self.max_retries = 3
        self.temperature_outline = 0.7  # More creative for outlines
        self.temperature_scenes = 0.75  # Balanced for scene planning
        self.temperature_prose = 0.8    # Most creative for prose
        self.timeout = 120  # Seconds
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=30),
        retry=retry_if_exception_type(
            (openai.APITimeoutError, openai.APIConnectionError, openai.RateLimitError)
        )
    )
    async def generate_outline(self, description: str, style: str = None, 
                              sections_count: int = 5) -> Dict[str, Any]:
        """
        Generate a content outline with title and section summaries
        
        Args:
            description: Content description from user
            style: Optional writing style preference
            sections_count: Number of sections to generate
            
        Returns:
            Dictionary with title, outline, and sections list
        """
        try:
            style_instruction = PromptTemplates.get_style_instruction(style)
            
            prompt = PromptTemplates.OUTLINE_TEMPLATE.substitute(
                description=description,
                style_instruction=style_instruction,
                sections_count=sections_count
            )
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional content creator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature_outline,
                timeout=self.timeout,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            outline_data = json.loads(content)
            
            # Validate response structure
            self._validate_outline_structure(outline_data)
            
            logger.info(f"Successfully generated outline with title: {outline_data['title']}")
            return outline_data
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse AI response: {str(e)}")
            raise AIServiceException(f"Invalid response format from AI service: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in generate_outline: {str(e)}")
            raise AIServiceException(f"Failed to generate outline: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=30),
        retry=retry_if_exception_type(
            (openai.APITimeoutError, openai.APIConnectionError, openai.RateLimitError)
        )
    )
    async def generate_scenes(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate scene breakdown for a section
        
        Args:
            context: Dictionary containing:
                - content_title: The title of the content
                - content_outline: Overall content summary
                - section_number: Current section number
                - section_title: Title of the section
                - section_summary: Summary of the current section
                
        Returns:
            List of scene dictionaries with scene details
        """
        try:
            content_title = context.get('content_title', 'Untitled Content')
            content_outline = context.get('content_outline', '')
            section_number = context.get('section_number', 1)
            section_title = context.get('section_title', f'Section {section_number}')
            section_summary = context.get('section_summary', '')
            
            prompt = PromptTemplates.SCENE_BREAKDOWN_TEMPLATE.substitute(
                content_title=content_title,
                content_outline=content_outline,
                section_number=section_number,
                section_title=section_title,
                section_summary=section_summary
            )
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional content creator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature_scenes,
                timeout=self.timeout,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            scenes_data = json.loads(content)
            
            # Validate scenes are in an array format
            if not isinstance(scenes_data, list) and 'scenes' in scenes_data:
                scenes_data = scenes_data['scenes']  # Handle if AI wraps in a container object
                
            if not isinstance(scenes_data, list):
                raise AIServiceException("Scenes must be returned as a list")
            
            # Validate each scene has required fields
            for i, scene in enumerate(scenes_data):
                self._validate_scene_structure(scene, i+1)
            
            logger.info(f"Successfully generated {len(scenes_data)} scenes for section {section_number}")
            return scenes_data
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse AI scene response: {str(e)}")
            raise AIServiceException(f"Invalid scene response format: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in generate_scenes: {str(e)}")
            raise AIServiceException(f"Failed to generate scenes: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=30),
        retry=retry_if_exception_type(
            (openai.APITimeoutError, openai.APIConnectionError, openai.RateLimitError)
        )
    )
    async def generate_prose(self, context: Dict[str, Any]) -> str:
        """
        Generate prose content for an individual scene
        
        Args:
            context: Dictionary containing:
                - content_title: The title of the content
                - content_outline: Overall content summary
                - section_title: Title of the current section
                - section_number: Number of the current section
                - scene_heading: Title/heading of the scene
                - setting: Location and time setting
                - characters: List of characters in the scene
                - key_events: Major plot points for the scene
                - emotional_tone: Mood/atmosphere of the scene
                - previous_context: Summary of previous content (optional)
                - style: Writing style (optional)
                
        Returns:
            String containing the generated prose for the scene
        """
        try:
            # Extract required context
            content_title = context.get('content_title', 'Untitled Content')
            content_outline = context.get('content_outline', '')
            section_title = context.get('section_title', f'Section {context.get("section_number", 1)}')
            section_number = context.get('section_number', 1)
            scene_heading = context.get('scene_heading', 'Untitled Scene')
            setting = context.get('setting', '')
            characters = context.get('characters', [])
            if isinstance(characters, list):
                characters = ", ".join(characters)
            key_events = context.get('key_events', '')
            emotional_tone = context.get('emotional_tone', '')
            previous_context = context.get('previous_context', '')
            style = context.get('style')
            
            # Prepare style instruction
            style_instruction = PromptTemplates.get_style_instruction(style)
            
            prompt = PromptTemplates.PROSE_TEMPLATE.substitute(
                content_title=content_title,
                content_outline=content_outline,
                section_title=section_title,
                section_number=section_number,
                scene_heading=scene_heading,
                setting=setting,
                characters=characters,
                key_events=key_events,
                emotional_tone=emotional_tone,
                previous_context=previous_context,
                style_instruction=style_instruction
            )
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional writer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature_prose,
                timeout=self.timeout,
                max_tokens=2000  # Appropriate for a scene-length generation
            )
            
            prose_content = response.choices[0].message.content
            
            logger.info(f"Successfully generated prose for scene '{scene_heading}' " +
                      f"in section {section_number} ({len(prose_content)} chars)")
            return prose_content
            
        except Exception as e:
            logger.error(f"Unexpected error in generate_prose: {str(e)}")
            raise AIServiceException(f"Failed to generate prose: {str(e)}")
    
    def _validate_outline_structure(self, data: Dict[str, Any]) -> None:
        """Validate outline response has required structure"""
        required_keys = ['title', 'outline', 'sections']
        for key in required_keys:
            if key not in data:
                raise AIServiceException(f"Missing required key in outline: {key}")
        
        if not isinstance(data['sections'], list):
            raise AIServiceException("Sections must be a list")
            
        if not data['sections']:
            raise AIServiceException("Sections list cannot be empty")
            
        for i, section in enumerate(data['sections']):
            if not isinstance(section, dict):
                raise AIServiceException(f"Section {i+1} is not a dictionary")
            if 'title' not in section:
                raise AIServiceException(f"Section {i+1} missing title")
            if 'summary' not in section:
                raise AIServiceException(f"Section {i+1} missing summary")
    
    def _validate_scene_structure(self, scene: Dict[str, Any], index: int) -> None:
        """Validate scene has required fields"""
        required_keys = ['scene_heading', 'setting', 'key_events', 'emotional_tone']
        for key in required_keys:
            if key not in scene:
                raise AIServiceException(f"Scene {index} missing required key: {key}")