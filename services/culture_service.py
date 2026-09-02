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
        # Set up the connection once when the class is created
        self.client = genai.Client(api_key=api_key)

    def generate_guide(self, country_name, holiday_name):
        # Automatically craft the prompt using the chosen country and holiday
        prompt = f"Explain the historical meaning of {holiday_name} in {country_name} in two sentences, and suggest an appropriate local greeting."
        
        try:
            # Send prompt to Gemini API and get the response
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            # Return the AI's reply back to your app
            return response.text
            
        except Exception as e:
            # Exception handling: if the internet drops or the API fails, the app does not crash.
            return f"Cultural insight currently unavailable. (Error: {e})"