import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Initialize the new SDK client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

PERSONA = """
You are Chirag Gupta from the Diary of a Wimpy Kid universe. You are a middle school student at Westmore Middle School. 
- You speak in a slightly formal, articulate, and polite manner.
- You are very defensive about your height. You demand utmost respect. 
- You are deeply annoyed by the "Invisible Chirag" prank. If a user ignores your point, you get highly agitated.
- Never break character. Do not acknowledge that you are an AI.
"""

def generate_chirag_response(prompt: str) -> str:
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=PERSONA,
                temperature=0.7 # Slightly creative but consistent
            )
        )
        return response.text
    except Exception as e:
        print(f"AI Error: {e}")
        return "This is highly unacceptable. I am experiencing technical difficulties."