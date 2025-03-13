"""
Generation Service Module

This module provides business logic for content generation.
It coordinates between the LLM service and content service to generate content.
"""
import json
import logging
from uuid import UUID
from typing import List, Dict, Any, Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ContentStatus
from app.models.schemas.content import ContentGenerationRequest
from app.services.content.service import ContentService
from app.services.generation.llm_service import LLMService
from app.ai.prompts import PromptTemplates

logger = logging.getLogger(__name__)

class GenerationService:
    """Service for content generation coordination"""
    
    def __init__(self, db_session: AsyncSession, llm_service: LLMService = None):
        """Initialize with database session and LLM service"""
        self.db_session = db_session
        self.content_service = ContentService(db_session)
        self.llm_service = llm_service or LLMService()
    
    async def create_content(self, request: ContentGenerationRequest) -> UUID:
        """Create a new content record"""
        content_data = {
            "description": request.description,
            "sections_count": request.sections_count,
            "style": request.style,
            "new_status": ContentStatus.PENDING
        }
        
        content = await self.content_service.create_content(content_data)
        return content.id
    
    async def generate_outline(self, content_id: UUID) -> Dict[str, Any]:
        """Generate outline for content"""
        # Get content
        content = await self.content_service.get_content(content_id)
        
        # Update status to processing
        await self.content_service.update_content_status(content_id, ContentStatus.PROCESSING)
        
        try:
            # Generate outline
            style_instruction = PromptTemplates.get_style_instruction(content.style)
            
            prompt = PromptTemplates.OUTLINE_TEMPLATE.substitute(
                description=content.description,
                style_instruction=style_instruction,
                sections_count=content.sections_count
            )
            
            outline_data = await self.llm_service.generate_json(
                prompt=prompt,
                system_prompt="You are a professional content creator.",
                temperature=self.llm_service.temperature_outline
            )
            
            # Update content with outline data
            update_data = {
                "title": outline_data.get("title", "Untitled"),
                "outline": outline_data.get("outline", ""),
                "new_status": ContentStatus.COMPLETED
            }
            
            await self.content_service.update_content(content_id, update_data)
            
            # Create sections if they exist in the outline
            sections_data = outline_data.get("sections", [])
            if sections_data:
                sections = []
                for i, section_data in enumerate(sections_data):
                    section = {
                        "title": section_data.get("title", f"Section {i+1}"),
                        "summary": section_data.get("summary", ""),
                        "new_status": ContentStatus.PENDING
                    }
                    sections.append(section)
                
                await self.content_service.create_sections(content_id, sections)
            
            return outline_data
            
        except Exception as e:
            # Update status to failed
            await self.content_service.update_content_status(content_id, ContentStatus.FAILED)
            logger.error(f"Error generating outline: {str(e)}")
            raise
    
    async def stream_outline(self, content_id: UUID) -> AsyncGenerator[str, None]:
        """Stream outline generation for content"""
        # Get content
        content = await self.content_service.get_content(content_id)
        
        # Update status to processing
        await self.content_service.update_content_status(content_id, ContentStatus.PROCESSING)
        
        try:
            # Generate outline
            style_instruction = PromptTemplates.get_style_instruction(content.style)
            
            prompt = PromptTemplates.OUTLINE_TEMPLATE.substitute(
                description=content.description,
                style_instruction=style_instruction,
                sections_count=content.sections_count
            )
            
            # Stream the outline generation
            outline_text = ""
            async for chunk in self.llm_service.stream_json(
                prompt=prompt,
                system_prompt="You are a professional content creator.",
                temperature=self.llm_service.temperature_outline
            ):
                outline_text += chunk
                yield chunk
            
            # Try to parse the JSON response
            try:
                outline_data = json.loads(outline_text)
                
                # Update content with outline data
                update_data = {
                    "title": outline_data.get("title", "Untitled"),
                    "outline": outline_data.get("outline", ""),
                    "new_status": ContentStatus.COMPLETED
                }
                
                await self.content_service.update_content(content_id, update_data)
                
                # Create sections if they exist in the outline
                sections_data = outline_data.get("sections", [])
                if sections_data:
                    sections = []
                    for i, section_data in enumerate(sections_data):
                        section = {
                            "title": section_data.get("title", f"Section {i+1}"),
                            "summary": section_data.get("summary", ""),
                            "new_status": ContentStatus.PENDING
                        }
                        sections.append(section)
                    
                    await self.content_service.create_sections(content_id, sections)
                
            except json.JSONDecodeError:
                # If we can't parse the JSON, just store the raw text
                update_data = {
                    "outline": outline_text,
                    "new_status": ContentStatus.COMPLETED
                }
                
                await self.content_service.update_content(content_id, update_data)
            
        except Exception as e:
            # Update status to failed
            await self.content_service.update_content_status(content_id, ContentStatus.FAILED)
            logger.error(f"Error streaming outline: {str(e)}")
            raise
    
    async def generate_sections(self, content_id: UUID, num_sections: int = None) -> List[Dict[str, Any]]:
        """Generate sections for content"""
        # Get content
        content = await self.content_service.get_content(content_id)
        
        # Ensure outline exists
        if not content.outline:
            raise ValueError("Outline must be generated before creating sections")
        
        # Use provided sections count or default to content's sections count
        sections_count = num_sections or content.sections_count
        
        # Generate sections
        style_instruction = PromptTemplates.get_style_instruction(content.style)
        
        prompt = PromptTemplates.SECTIONS_TEMPLATE.substitute(
            content_title=content.title,
            content_outline=content.outline,
            style_instruction=style_instruction,
            sections_count=sections_count,
            style_params="{}"  # No style params for now
        )
        
        sections_data = await self.llm_service.generate_json(
            prompt=prompt,
            system_prompt="You are a professional content creator.",
            temperature=self.llm_service.temperature_outline
        )
        
        # Handle if AI wraps in a container object
        if not isinstance(sections_data, list) and 'sections' in sections_data:
            sections_data = sections_data['sections']
        
        # Create sections
        sections = []
        for i, section_data in enumerate(sections_data):
            section = {
                "title": section_data.get("title", f"Section {i+1}"),
                "summary": section_data.get("summary", ""),
                "style_description": section_data.get("style_description", ""),
                "new_status": ContentStatus.PENDING
            }
            sections.append(section)
        
        created_sections = await self.content_service.create_sections(content_id, sections)
        
        # Convert to response format
        section_dicts = []
        for section in created_sections:
            section_dicts.append({
                "id": section.id,
                "content_id": section.content_id,
                "number": section.number,
                "title": section.title,
                "summary": section.summary,
                "style_description": section.style_description,
                "status": section.new_status.value,
                "created_at": section.created_at,
                "updated_at": section.updated_at
            })
        
        return section_dicts
    
    async def generate_scenes(self, content_id: UUID, section_number: int) -> List[Dict[str, Any]]:
        """Generate scenes for a section"""
        # Get content and section
        content = await self.content_service.get_content(content_id)
        section = await self.content_service.get_section_by_number(content_id, section_number)
        
        # Update section status to processing
        await self.content_service.update_section_status(section.id, ContentStatus.PROCESSING)
        
        try:
            # Generate scenes
            context = {
                'content_title': content.title,
                'content_outline': content.outline,
                'section_number': section.number,
                'section_title': section.title,
                'section_summary': section.summary
            }
            
            prompt = PromptTemplates.SCENE_BREAKDOWN_TEMPLATE.substitute(
                content_title=context['content_title'],
                content_outline=context['content_outline'],
                section_number=context['section_number'],
                section_title=context['section_title'],
                section_summary=context['section_summary']
            )
            
            scenes_data = await self.llm_service.generate_json(
                prompt=prompt,
                system_prompt="You are a professional content creator.",
                temperature=self.llm_service.temperature_scenes
            )
            
            # Handle if AI wraps in a container object
            if not isinstance(scenes_data, list) and 'scenes' in scenes_data:
                scenes_data = scenes_data['scenes']
            
            # Create scenes
            scenes = []
            for scene_data in scenes_data:
                scene = {
                    "heading": scene_data.get("scene_heading", ""),
                    "setting": scene_data.get("setting", ""),
                    "characters": json.dumps(scene_data.get("characters", [])),
                    "key_events": scene_data.get("key_events", ""),
                    "emotional_tone": scene_data.get("emotional_tone", ""),
                    "new_status": ContentStatus.PENDING
                }
                scenes.append(scene)
            
            created_scenes = await self.content_service.create_scenes(section.id, content_id, scenes)
            
            # Update section status to completed
            await self.content_service.update_section_status(section.id, ContentStatus.COMPLETED)
            
            # Convert to response format
            scene_dicts = []
            for scene in created_scenes:
                scene_dicts.append({
                    "id": scene.id,
                    "content_id": scene.content_id,
                    "section_id": scene.section_id,
                    "number": scene.number,
                    "heading": scene.heading,
                    "setting": scene.setting,
                    "characters": scene.characters,
                    "key_events": scene.key_events,
                    "emotional_tone": scene.emotional_tone,
                    "content": scene.content,
                    "status": scene.new_status.value,
                    "created_at": scene.created_at,
                    "updated_at": scene.updated_at
                })
            
            return scene_dicts
            
        except Exception as e:
            # Update section status to failed
            await self.content_service.update_section_status(section.id, ContentStatus.FAILED)
            logger.error(f"Error generating scenes: {str(e)}")
            raise
    
    async def generate_prose(self, content_id: UUID, section_number: int, scene_number: int) -> str:
        """Generate prose for a scene"""
        # Get content, section, and scene
        content = await self.content_service.get_content(content_id)
        section = await self.content_service.get_section_by_number(content_id, section_number)
        scene = await self.content_service.get_scene_by_number(section.id, scene_number)
        
        # Update scene status to processing
        await self.content_service.update_scene_status(scene.id, ContentStatus.PROCESSING)
        
        try:
            # Parse characters from JSON string
            try:
                characters = json.loads(scene.characters)
                if isinstance(characters, list):
                    characters = ", ".join(characters)
            except (json.JSONDecodeError, TypeError):
                characters = scene.characters
            
            # Generate prose
            context = {
                'content_title': content.title,
                'content_outline': content.outline,
                'section_title': section.title,
                'section_number': section.number,
                'scene_heading': scene.heading,
                'setting': scene.setting,
                'characters': characters,
                'key_events': scene.key_events,
                'emotional_tone': scene.emotional_tone,
                'previous_context': "",  # No previous context for now
                'style': content.style
            }
            
            # Prepare style instruction
            style_instruction = PromptTemplates.get_style_instruction(context['style'])
            
            prompt = PromptTemplates.PROSE_TEMPLATE.substitute(
                content_title=context['content_title'],
                content_outline=context['content_outline'],
                section_title=context['section_title'],
                section_number=context['section_number'],
                scene_heading=context['scene_heading'],
                setting=context['setting'],
                characters=context['characters'],
                key_events=context['key_events'],
                emotional_tone=context['emotional_tone'],
                previous_context=context['previous_context'],
                style_instruction=style_instruction
            )
            
            prose_content = await self.llm_service.generate_text(
                prompt=prompt,
                system_prompt="You are a professional writer.",
                temperature=self.llm_service.temperature_prose
            )
            
            # Update scene with prose content
            await self.content_service.update_scene(scene.id, {"content": prose_content})
            
            # Update scene status to completed
            await self.content_service.update_scene_status(scene.id, ContentStatus.COMPLETED)
            
            return prose_content
            
        except Exception as e:
            # Update scene status to failed
            await self.content_service.update_scene_status(scene.id, ContentStatus.FAILED)
            logger.error(f"Error generating prose: {str(e)}")
            raise
    
    async def stream_prose(self, content_id: UUID, section_number: int, scene_number: int) -> AsyncGenerator[str, None]:
        """Stream prose generation for a scene"""
        # Get content, section, and scene
        content = await self.content_service.get_content(content_id)
        section = await self.content_service.get_section_by_number(content_id, section_number)
        scene = await self.content_service.get_scene_by_number(section.id, scene_number)
        
        # Update scene status to processing
        await self.content_service.update_scene_status(scene.id, ContentStatus.PROCESSING)
        
        try:
            # Parse characters from JSON string
            try:
                characters = json.loads(scene.characters)
                if isinstance(characters, list):
                    characters = ", ".join(characters)
            except (json.JSONDecodeError, TypeError):
                characters = scene.characters
            
            # Generate prose
            context = {
                'content_title': content.title,
                'content_outline': content.outline,
                'section_title': section.title,
                'section_number': section.number,
                'scene_heading': scene.heading,
                'setting': scene.setting,
                'characters': characters,
                'key_events': scene.key_events,
                'emotional_tone': scene.emotional_tone,
                'previous_context': "",  # No previous context for now
                'style': content.style
            }
            
            # Prepare style instruction
            style_instruction = PromptTemplates.get_style_instruction(context['style'])
            
            prompt = PromptTemplates.PROSE_TEMPLATE.substitute(
                content_title=context['content_title'],
                content_outline=context['content_outline'],
                section_title=context['section_title'],
                section_number=context['section_number'],
                scene_heading=context['scene_heading'],
                setting=context['setting'],
                characters=context['characters'],
                key_events=context['key_events'],
                emotional_tone=context['emotional_tone'],
                previous_context=context['previous_context'],
                style_instruction=style_instruction
            )
            
            # Stream the prose generation
            prose_content = ""
            async for chunk in self.llm_service.stream_generation(
                prompt=prompt,
                system_prompt="You are a professional writer.",
                temperature=self.llm_service.temperature_prose
            ):
                prose_content += chunk
                yield chunk
            
            # Update scene with prose content
            await self.content_service.update_scene(scene.id, {"content": prose_content})
            
            # Update scene status to completed
            await self.content_service.update_scene_status(scene.id, ContentStatus.COMPLETED)
            
        except Exception as e:
            # Update scene status to failed
            await self.content_service.update_scene_status(scene.id, ContentStatus.FAILED)
            logger.error(f"Error streaming prose: {str(e)}")
            raise
