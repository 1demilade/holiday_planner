"""
culture_service.py

Gets cultural information from Gemini
"""

## WORKFLOW
## Holiday Object -> CultureGuideGenerator -> Gemini API -> Cultural Guide

# This service should also be responsible for prompt generation

from google import genai
from collections.abc import Iterator

class CultureGuideGenerator:
    """Gets cultural information from Gemini for a given holiday."""

    def __init__(self, api_key: str):
        api_key = (api_key or "").strip()
        if not api_key:
            raise ValueError("Gemini API key is required.")
        
        self.client = genai.Client(api_key=api_key)


    def get_cultural_guide(self, holiday_name: str, country_code: str) -> Iterator[str]:
        """Generates a cultural guide for a given holiday and country code using the Gemini API."""

        prompt = f"Summarize the holiday '{holiday_name}' ({country_code}) in brief Markdown covering: Cultural Significance, Traditions & Customs, and Local Greeting."
        
        try:
            response_stream = self.client.models.generate_content_stream(
                model="gemini-3.5-flash-lite",
                contents=prompt
            )

            # streaming output means we can yield each chunk of text as it arrives, allowing for real-time display in the UI.
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text

        except Exception as error:
            raise RuntimeError(f"Gemini request failed: {error}") from error
