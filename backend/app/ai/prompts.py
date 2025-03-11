# app/ai/prompts.py
from string import Template

class PromptTemplates:
    """Collection of prompt templates for content generation"""
    
    OUTLINE_TEMPLATE = Template("""
    You are a professional content creator tasked with creating a compelling outline.
    
    CONTENT DESCRIPTION:
    $description
    
    ${style_instruction}
    
    Provide a comprehensive outline with:
    1. An engaging title
    2. A brief summary of the overall content (250-300 words)
    3. A list of $sections_count sections with:
       - Section title
       - Brief section summary (50-100 words each)
    
    Format your response as a JSON object with the structure:
    {
      "title": "Content Title",
      "outline": "Overall summary...",
      "sections": [
        {"title": "Section 1 Title", "summary": "Section 1 summary..."},
        {"title": "Section 2 Title", "summary": "Section 2 summary..."}
      ]
    }
    """)

    SECTIONS_TEMPLATE = Template("""
    You are a content creator tasked with creating detailed sections for a piece titled "$content_title".

    Content Outline:
    $content_outline

    Based on this outline, generate $sections_count detailed sections. Each section should have:
    1. A clear, descriptive title
    2. A comprehensive summary of what the section will contain
    3. A style description that explains the writing style, tone, and approach for this specific section

    $style_instruction

    Format your response as a JSON array of section objects with the following structure:
    [
      {
        "title": "Section Title",
        "summary": "Detailed summary of the section content",
        "style_description": "Description of the writing style for this section"
      },
      ...
    ]
    """)
    
    SCENE_BREAKDOWN_TEMPLATE = Template("""
    You are a professional content creator working on "$content_title".
    
    You need to break down section $section_number: "$section_title" into 3-5 distinct scenes.
    
    SECTION CONTEXT:
    - Overall content summary: $content_outline
    - This section covers: $section_summary
    
    For each scene, provide:
    1. A brief scene heading/title
    2. Setting description (where and when)
    3. Characters involved (if applicable)
    4. Key plot points and developments
    5. Emotional tone or atmosphere
    
    Format your response as a JSON array of scene objects:
    [
      {
        "scene_heading": "Scene 1 Title",
        "setting": "Location and time of day",
        "characters": ["Character 1", "Character 2"],
        "key_events": "What happens in this scene",
        "emotional_tone": "The feeling/atmosphere of this scene"
      },
      {
        "scene_heading": "Scene 2 Title",
        "setting": "Location and time of day",
        "characters": ["Character 1", "Character 3"],
        "key_events": "What happens in this scene",
        "emotional_tone": "The feeling/atmosphere of this scene" 
      }
    ]
    
    Ensure the scenes flow logically and cover the entire section content.
    """)
    
    PROSE_TEMPLATE = Template("""
    You are a professional content creator writing "$content_title".
    
    CURRENT SCENE DETAILS:
    - Section: $section_title (section $section_number)
    - Scene heading: $scene_heading
    - Setting: $setting
    - Characters: $characters
    - Key events: $key_events
    - Emotional tone: $emotional_tone
    
    CONTEXT:
    - Overall content: $content_outline
    - Previous content context: $previous_context
    
    ${style_instruction}
    
    Write an engaging, immersive scene of approximately 500-800 words. Your writing should:
    - Begin with vivid scene-setting that establishes the location and mood
    - Develop characters through dialogue and action
    - Include sensory details and descriptive elements
    - Advance the plot points specified in the key events
    - Maintain the specified emotional tone throughout
    - End with an appropriate transition to the next scene
    
    Focus on showing rather than telling. Use specific details rather than generalizations.
    """)
    
    # Style adaptation dictionary remains the same
    STYLE_ADAPTATION = {
        "literary": "Write in a literary style with rich imagery, complex characters, and thematic depth. Use elegant prose similar to authors like Toni Morrison or Ian McEwan.",
        # Other styles remain the same
    }
    
    @classmethod
    def get_style_instruction(cls, style: str = None) -> str:
        """Get style-specific instructions or empty string if no style specified"""
        if not style:
            return ""
            
        style = style.lower()
        if style in cls.STYLE_ADAPTATION:
            return f"WRITING STYLE:\n{cls.STYLE_ADAPTATION[style]}"
        else:
            return f"WRITING STYLE:\nWrite in a style that resembles {style}."