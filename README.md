# Chirag Discord Bot

An AI-powered Discord bot built with Python, `discord.py`, and the Google Gemini API. 

The bot uses the `gemini-2.5-flash` model and is prompted to roleplay as **Chirag Gupta** from the *Diary of a Wimpy Kid* universe. It speaks formally, demands respect, and gets highly defensive if anyone attempts the "Invisible Chirag" prank.

## Tech Stack
* **Python 3.12+**
* **discord.py** - For interacting with the Discord API.
* **google-genai** - For generating AI responses using Gemini.
* **Flask** - A lightweight web server used to keep the bot alive on cloud hosts.

## Project Structure
* `main.py`: The entry point that connects to Discord and handles incoming messages.
* `ai_handler.py`: Isolates the Gemini API logic and system instructions (persona).
* `keep_alive.py`: Runs a background Flask server so cloud services don't put the bot to sleep.
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
4. Add your `DISCORD_TOKEN` and `GEMINI_API_KEY` to the Environment Variables tab on Render.
5. Copy the provided Render URL and create an HTTP monitor on UptimeRobot to ping it every 5 minutes. This prevents Render's free tier from putting the bot to sleep.

## Usage
Once the bot is online and in your server, you must directly `@mention` it to get a response:
> `@Chirag Are you there? I can't see you.`