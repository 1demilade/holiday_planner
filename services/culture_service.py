"""
culture_service.py

Gets cultural information from Gemini
"""

## WORKFLOW
## Holiday Object -> CultureGuideGenerator -> Gemini API -> Cultural Guide

# This service should also be responsible for prompt generation

from google import genai

class CultureGuideGenerator:
    def __init__(self, api_key):
        # 1. Set up the connection once when the class is created
        self.client = genai.Client(api_key=api_key)

    def generate_guide(self, country_name, holiday_name):
        # 2. Automatically craft the prompt using the chosen country and holiday
        prompt = f"Explain the historical meaning of {holiday_name} in {country_name} in two sentences, and suggest an appropriate local greeting."
        
        try:
            # 3. Hit 'Send' to the Gemini model
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            # 4. Return the AI's reply back to your app
            return response.text
            
        except Exception as e:
            # Exception handling: if the internet drops or the API fails, don't crash the app!
            return f"Cultural insight currently unavailable. (Error: {e})"