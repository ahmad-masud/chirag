from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "Chirag is alive and well."

def run():
    # Render assigns a dynamic port, so we must capture it
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()