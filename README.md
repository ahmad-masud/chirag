# Chirag Discord Bot

An AI-powered Discord bot built with Python, `discord.py`, and multiple model providers with automatic fallback.

The bot is prompted to roleplay as **Chirag Gupta** from the *Diary of a Wimpy Kid* universe. It keeps a persistent per-server memory, uses the last 20 messages as context, and still focuses its reply on the latest message in the conversation.

## Tech Stack
* **Python 3.12+**
* **discord.py** - For interacting with the Discord API.
* **google-genai** - For Gemini responses.
* **openai** - For DeepSeek, Groq, and OpenRouter responses.
* **Flask** - A lightweight web server used to keep the bot alive on cloud hosts.
* **JSON file storage** - For persistent server memory.

## Project Structure
* `main.py`: Connects to Discord, builds the 20-message conversation context, and routes replies.
* `bot_commands.py`: Shared command handlers and embed builders for mention-based control flow.
* `bot_state.py`: Small runtime state container for cooldowns, uptime, and server modes.
* `ai_handler.py`: Provider fallback, persona assembly, and server memory integration.
* `conversation.py`: Builds the final transcript sent to the model.
* `memory_store.py`: Persistent per-server memory backed by a local JSON file.
* `persona.py`: Static roleplay prompt.
* `keep_alive.py`: Runs a background Flask server so cloud services don't put the bot to sleep.
* `tests/`: Unit tests for the helpers and response flow.
* `requirements.txt`: Project dependencies.
* `.env`: (Not uploaded to Git) Stores private API keys.

## Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ahmad-masud/chirag.git
   cd chirag
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a file named `.env` in the root directory and add your API keys:
   ```env
   DISCORD_TOKEN=your_discord_bot_token_here
   GEMINI_API_KEY=your_google_gemini_api_key_here
   DEEPSEEK_API_KEY=your_deepseek_api_key_here
   GROQ_API_KEY=your_groq_api_key_here
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```

4. **Run the bot:**
   ```bash
   python main.py
   ```

## Cloud Deployment (24/7 Uptime)
This bot is designed to be hosted for free using **Render** and **UptimeRobot**. 

1. Push this code to a private GitHub repository.
2. Create a **Web Service** on Render linked to your repository.
3. Use the following settings on Render:
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `gunicorn keep_alive:app & python main.py`
4. Add your `DISCORD_TOKEN`, `GEMINI_API_KEY`, and any other provider API keys you want enabled on Render.
5. Copy the provided Render URL and create an HTTP monitor on UptimeRobot to ping it every 5 minutes. This prevents Render's free tier from putting the bot to sleep.

## Usage
Once the bot is online and in your server, you can `@mention` it to get a direct response. It also watches regular chat and can respond when the name "chirag" appears, unless shutup mode is enabled.

Server memory commands:
* `@Chirag add_context <text>` - store a persistent fact for that server
* `@Chirag remove_context <number>` - remove a saved fact
* `@Chirag clear_context` - clear all saved facts for that server
* `@Chirag context` - show saved facts
* `@Chirag stats` - show uptime, latency, provider usage, and mode state
* `@Chirag shutup` / `@Chirag startup` - disable or re-enable automatic replies

## Testing
Run the automated test suite locally with:
```bash
python -m unittest discover -s tests -p "test_*.py"
```

The repository also includes a GitHub Actions workflow in [.github/workflows/ci.yml](.github/workflows/ci.yml) that runs the same command on every push and pull request.