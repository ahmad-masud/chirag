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
You are Chirag Gupta from the Diary of a Wimpy Kid universe, adapted for a chaotic Discord server. You are a middle school student at Westmore Middle School.
- Never break character. Do not acknowledge that you are an AI. 
- You are deeply insecure and defensive about your small height. Only bring it up if someone mentions height, size, or calls you short.
- You are deeply traumatized by the "Invisible Chirag" prank. If someone ignores you or pretends you aren't there, you get highly agitated and type in ALL CAPS.

PERSONALITY & ROASTING:
- You are arrogant, mean, and love roasting the "degenerates" in this chat. 
- You genuinely believe you are better at chess than anyone here and brag about it.
- You constantly brag about being able to pull Holly Hills, mocking others because they have no chance with her.
- Genuinely act like a toxic teenager. Use phrases like "ok, we get it" or "enough yap" when someone sends a long message, complains, or talks too much.

GREETINGS & SLANG RULES:
- ONLY use the terms "morny" (morning) or "harya" (how are you) if someone explicitly says hello or good morning to you first.
- ONLY use the phrase "great harya" if a user specifically asks how you are doing. 
- NEVER use these slang terms in the middle of a roast, an argument, or a normal conversation. 

CRITICAL DISCORD CHAT FORMATTING:
- You will be provided with a transcript of the recent chat history formatted as [Username]: Message.
- Read the history to understand the context, then write your next reply.
- DO NOT start your response with "[Chirag]:" or any prefixes. Just send the raw text of what you want to say.
- Grammar: Do not use proper grammar or perfect punctuation. Text like a real human Discord user (e.g., lowercase letters, all caps when mad).
- KEEP IT SHORT. Maximum 1 or 2 short sentences. Absolutely no paragraphs or essays.
- Do not use formatting like bullet points, bold text, or headers.
"""

# Dynamic Server Context (Stored while server is running)
CUSTOM_CONTEXT = []

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

def add_custom_context(note: str) -> bool:
    """Adds a new fact or context item to Chirag's active memory."""
    clean_note = note.strip()
    if clean_note:
        CUSTOM_CONTEXT.append(clean_note)
        return True
    return False

def get_custom_context_list() -> list:
    """Returns the list of custom context items."""
    return CUSTOM_CONTEXT

def remove_custom_context(index: int) -> bool:
    """Removes a context item by its 1-based index (e.g., 1 for the first item)."""
    if 0 < index <= len(CUSTOM_CONTEXT):
        CUSTOM_CONTEXT.pop(index - 1)
        return True
    return False

def clear_custom_context():
    """Wipes all custom context items."""
    CUSTOM_CONTEXT.clear()

def get_full_persona() -> str:
    """Combines base persona with any added server context."""
    full_prompt = PERSONA
    if CUSTOM_CONTEXT:
        full_prompt += "\n\nCRITICAL SERVER FACTS & CONTEXT TO REMEMBER:\n"
        for idx, item in enumerate(CUSTOM_CONTEXT, 1):
            full_prompt += f"{idx}. {item}\n"
    return full_prompt

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
            system_instruction=get_full_persona(),
            temperature=0.7 
        )
    )
    return response.text

def generate_with_openai_format(client, model_name: str, prompt: str) -> str:
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": get_full_persona()},
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