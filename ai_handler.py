import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from openai import OpenAI
from persona import PERSONA
from memory_store import add_context, clear_context, get_context_list, remove_context

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

PROVIDER_SEQUENCE = ("deepseek", "openrouter", "gemini", "groq")


def _generate_for_provider(provider_name: str, server_id: int, prompt: str) -> str:
    if provider_name == "gemini":
        return generate_with_gemini(server_id, prompt)

    if provider_name == "deepseek":
        client = deepseek_client
        model_name = PROVIDER_MODELS["deepseek"]
    elif provider_name == "openrouter":
        client = openrouter_client
        model_name = PROVIDER_MODELS["openrouter"]
    elif provider_name == "groq":
        client = groq_client
        model_name = PROVIDER_MODELS["groq"]
    else:
        raise ValueError(f"Unknown provider: {provider_name}")

    return generate_with_openai_format(client, model_name, server_id, prompt)

def add_custom_context(server_id: int, note: str) -> bool:
    return add_context(server_id, note)

def get_custom_context_list(server_id: int) -> list:
    """Returns the list of custom context items for a specific server."""
    return get_context_list(server_id)

def remove_custom_context(server_id: int, index: int) -> bool:
    return remove_context(server_id, index)

def clear_custom_context(server_id: int):
    clear_context(server_id)

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

    if ACTIVE_PROVIDER not in PROVIDER_SEQUENCE:
        ACTIVE_PROVIDER = PROVIDER_SEQUENCE[0]

    start_index = PROVIDER_SEQUENCE.index(ACTIVE_PROVIDER)
    last_error = None

    for attempt in range(len(PROVIDER_SEQUENCE)):
        provider_name = PROVIDER_SEQUENCE[(start_index + attempt) % len(PROVIDER_SEQUENCE)]

        try:
            response = _generate_for_provider(provider_name, server_id, prompt)
            REQUEST_COUNTS[provider_name] += 1
            ACTIVE_PROVIDER = provider_name
            return response
        except Exception as exc:
            last_error = exc
            next_provider = PROVIDER_SEQUENCE[(start_index + attempt + 1) % len(PROVIDER_SEQUENCE)]
            print(f"{provider_name.title()} failed ({exc}). Switching active provider to {next_provider.title()}...")

    ACTIVE_PROVIDER = PROVIDER_SEQUENCE[0]
    raise Exception("All API providers have failed.") from last_error