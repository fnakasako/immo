from anthropic import Anthropic
from app.core.config import settings
from app.models.novel import StoryGenerationRequest, ChapterContent
import json

class AIService:
    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        