import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# --- Initialize API Clients ---
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# DeepSeek uses the standard OpenAI format
deepseek_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

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
- You will receive a chat transcript formatted as [Username]: Message. 
- VERY IMPORTANT: Your primary job is to reply directly to the VERY LAST message in the transcript. Use the older messages ONLY for background context.
- DO NOT repeat jokes or brags from your previous messages in the transcript. Move the conversation forward.
- If the last message is a question directed at you, answer it directly. Do not ignore it to talk about chess or Holly Hills unless it makes sense for that specific message.
- DO NOT start your response with "[Chirag]:" or any prefixes. Just send the raw text of what you want to say.
- Grammar: Do not use proper grammar or perfect punctuation. Text like a real human Discord user (e.g., lowercase letters, all caps when mad).
- KEEP IT SHORT. Maximum 1 or 2 short sentences. Absolutely no paragraphs or essays.
- Do not use formatting like bullet points, bold text, or headers.
"""

# Dynamic Server Context (Dictionary mapped by server_id)
SERVER_CONTEXTS = {}

# Provider Tracking & Statistics (DeepSeek is the primary active provider)
ACTIVE_PROVIDER = "deepseek"
PROVIDER_MODELS = {
    "deepseek": "deepseek-v4-flash",
    "gemini": "gemini-3-flash",
    "groq": "meta-llama/llama-4-scout-17b-16e-instruct",
    "openrouter": "openai/gpt-oss-20b:free"
}
REQUEST_COUNTS = {
    "deepseek": 0,
    "gemini": 0,
    "groq": 0,
    "openrouter": 0
}

def add_custom_context(server_id: int, note: str) -> bool:
    """Adds a new fact to a specific server's memory."""
    clean_note = note.strip()
    if clean_note:
        if server_id not in SERVER_CONTEXTS:
            SERVER_CONTEXTS[server_id] = []
        SERVER_CONTEXTS[server_id].append(clean_note)
        return True
    return False

def get_custom_context_list(server_id: int) -> list:
    """Returns the list of custom context items for a specific server."""
    return SERVER_CONTEXTS.get(server_id, [])

def remove_custom_context(server_id: int, index: int) -> bool:
    """Removes a context item by its 1-based index for a specific server."""
    if server_id in SERVER_CONTEXTS and 0 < index <= len(SERVER_CONTEXTS[server_id]):
        SERVER_CONTEXTS[server_id].pop(index - 1)
        return True
    return False

def clear_custom_context(server_id: int):
    """Wipes all custom context items for a specific server."""
    if server_id in SERVER_CONTEXTS:
        SERVER_CONTEXTS[server_id].clear()

def get_full_persona(server_id: int) -> str:
    """Combines base persona with the specific server's context."""
    full_prompt = PERSONA
    context_list = get_custom_context_list(server_id)
    if context_list:
        full_prompt += "\n\nCRITICAL SERVER FACTS & CONTEXT TO REMEMBER:\n"
        for idx, item in enumerate(context_list, 1):
            full_prompt += f"{idx}. {item}\n"
    return full_prompt

def get_ai_stats():
    """Returns information about the current AI configuration and usage."""
    return {
        "active_provider": ACTIVE_PROVIDER.capitalize(),
        "active_model": PROVIDER_MODELS.get(ACTIVE_PROVIDER, "Unknown"),
        "request_counts": REQUEST_COUNTS
    }

def generate_with_gemini(server_id: int, prompt: str) -> str:
    response = gemini_client.models.generate_content(
        model=PROVIDER_MODELS["gemini"],
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=get_full_persona(server_id),
            temperature=0.7 
        )
    )
    return response.text

def generate_with_openai_format(client, model_name: str, server_id: int, prompt: str) -> str:
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": get_full_persona(server_id)},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content

def generate_chirag_response(server_id: int, prompt: str) -> str:
    global ACTIVE_PROVIDER
    
    # 1. DeepSeek Block
    if ACTIVE_PROVIDER == "deepseek":
        try:
            res = generate_with_openai_format(
                deepseek_client, 
                PROVIDER_MODELS["deepseek"], 
                server_id,
                prompt
            )
            REQUEST_COUNTS["deepseek"] += 1
            return res
        except Exception as e:
            print(f"DeepSeek failed ({e}). Switching active provider to OpenRouter...")
            ACTIVE_PROVIDER = "openrouter"

    # 2. OpenRouter Block
    if ACTIVE_PROVIDER == "openrouter":
        try:
            res = generate_with_openai_format(
                openrouter_client, 
                PROVIDER_MODELS["openrouter"], 
                server_id,
                prompt
            )
            REQUEST_COUNTS["openrouter"] += 1
            return res
        except Exception as e:
            print(f"OpenRouter failed ({e}). Switching active provider to Gemini...")
            ACTIVE_PROVIDER = "gemini"

    # 3. Gemini Block
    if ACTIVE_PROVIDER == "gemini":
        try:
            res = generate_with_gemini(server_id, prompt)
            REQUEST_COUNTS["gemini"] += 1
            return res
        except Exception as e:
            print(f"Gemini failed ({e}). Switching active provider to Groq...")
            ACTIVE_PROVIDER = "groq"

    # 4. Groq Block
    if ACTIVE_PROVIDER == "groq":
        try:
            res = generate_with_openai_format(
                groq_client, 
                PROVIDER_MODELS["groq"], 
                server_id,
                prompt
            )
            REQUEST_COUNTS["groq"] += 1
            return res
        except Exception as e:
            print(f"Groq failed ({e}). All providers exhausted.")
            ACTIVE_PROVIDER = "deepseek" # Reset back to top of the chain
            raise Exception("All API providers have failed.")