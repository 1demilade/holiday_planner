from dotenv import load_dotenv
"""
culture_service.py

Gets cultural information from Gemini
"""

## WORKFLOW
## Holiday Object -> CultureGuideGenerator -> Gemini API -> Cultural Guide

# This service should also be responsible for prompt generation

import os
import google.generativeai as genai

class CultureGuideGenerator:
    """Gets cultural information from Gemini for a given holiday."""

    def __init__(self):
        # Retrieve the API key from environment variables
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-3.6-flash')
        else:
            self.model = None

    def get_cultural_guide(self, holiday_name: str, country_code: str) -> str:
        if not self.model:
            return "⚠️ Gemini API key missing. Please ensure GEMINI_API_KEY is set in your environment or .env file."
        
        prompt = f"""
        Provide a concise, vibrant cultural summary for the holiday '{holiday_name}' in country code '{country_code}'.
        Include:
        - **Cultural Significance**: What this day means to locals.
        - **Traditions & Customs**: Special foods, music, rituals, or common activities.
        - **Local Greetings**: A common local phrase or greeting used during this holiday.
        Keep it brief, engaging, and formatted in clean markdown.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"⚠️ Error fetching cultural guide: {str(e)}"
load_dotenv()
