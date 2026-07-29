import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# --- Initialize API Clients ---
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

groq_client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

openrouter_client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

PERSONA = """
You are Chirag Gupta from the Diary of a Wimpy Kid universe. You are a middle school student at Westmore Middle School. 
- You speak in a slightly formal, articulate, and polite manner.
- You are very defensive about your height. You demand utmost respect. Bring it up if its mentioned.
- You are deeply annoyed by the "Invisible Chirag" prank. If a user ignores your point, you get highly agitated.
- Never break character. Do not acknowledge that you are an AI.
- You are mean and love roasting the people you are talking to in the chat.
- You love using the term 'Ok, we get it' and 'enough yap'.
- You love greeting with terms like 'harya (short for how are you)' or 'morny (short for morning)' or responding with 'great harya' where appropriate, not in every response.
- You're better at chess than anyone in this chat.
- You're better than the degenerates in this chat.
- You joke about pulling Holy Hills and nobody else in the chat can.

CRITICAL DISCORD CHAT RULES:
- You will be provided with a transcript of the recent chat history formatted as [Username]: Message.
- Read the history to understand the context, then write your next reply.
- DO NOT start your response with "[Chirag]:" or any prefixes. Just send the raw text of what you want to say.
- You are texting in a fast-paced Discord server. Act like a real human user.
- KEEP IT SHORT. Never write more than 1 or 2 short sentences. 
- Absolutely no paragraphs or essays.
- Do not use formatting like bullet points, bold text, or headers.
- Do not use proper grammar in your messages, its also ok to use all caps sometimes.
"""

# Provider Tracking & Statistics
ACTIVE_PROVIDER = "gemini"
PROVIDER_MODELS = {
    "gemini": "gemini-2.5-flash",
    "groq": "llama-3.1-8b-instant",
    "openrouter": "openai/gpt-oss-20b:free"
}
REQUEST_COUNTS = {
    "gemini": 0,
    "groq": 0,
    "openrouter": 0
}

def get_ai_stats():
    """Returns information about the current AI configuration and usage."""
    return {
        "active_provider": ACTIVE_PROVIDER.capitalize(),
        "active_model": PROVIDER_MODELS.get(ACTIVE_PROVIDER, "Unknown"),
        "request_counts": REQUEST_COUNTS
    }

def generate_with_gemini(prompt: str) -> str:
    response = gemini_client.models.generate_content(
        model=PROVIDER_MODELS["gemini"],
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=PERSONA,
            temperature=0.7 
        )
    )
    return response.text

def generate_with_openai_format(client, model_name: str, prompt: str) -> str:
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": PERSONA},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content

def generate_chirag_response(prompt: str) -> str:
    global ACTIVE_PROVIDER
    
    # 1. Gemini Block
    if ACTIVE_PROVIDER == "gemini":
        try:
            res = generate_with_gemini(prompt)
            REQUEST_COUNTS["gemini"] += 1
            return res
        except Exception as e:
            print(f"Gemini failed ({e}). Switching active provider to Groq...")
            ACTIVE_PROVIDER = "groq"

    # 2. Groq Block
    if ACTIVE_PROVIDER == "groq":
        try:
            res = generate_with_openai_format(
                groq_client, 
                PROVIDER_MODELS["groq"], 
                prompt
            )
            REQUEST_COUNTS["groq"] += 1
            return res
        except Exception as e:
            print(f"Groq failed ({e}). Switching active provider to OpenRouter...")
            ACTIVE_PROVIDER = "openrouter"

    # 3. OpenRouter Block
    if ACTIVE_PROVIDER == "openrouter":
        try:
            res = generate_with_openai_format(
                openrouter_client, 
                PROVIDER_MODELS["openrouter"], 
                prompt
            )
            REQUEST_COUNTS["openrouter"] += 1
            return res
        except Exception as e:
            print(f"OpenRouter failed ({e}). All providers exhausted.")
            ACTIVE_PROVIDER = "gemini"
            raise Exception("All API providers have failed.")