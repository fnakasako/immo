from anthropic import Anthropic
from app.core.config import settings
from app.models.novel import StoryGenerationRequest, ChapterContent
import json

class AIService:
    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def generate_story(self, request: StoryGenerationRequestion) -> List[ChapterContent]:
        chapters = []
    
        # Create the inital prompt for the story outline
        outline_prompt = self._create_outline_prompt(request)

        # Generate story outline
        outline_response = await self._generate_content(outline_prompt)

        # Generate each chapter
        for chapter_num in range(1, request.chapters +1):
            chapter_prompt = self._create_chapter_prompt(
                
            )
        