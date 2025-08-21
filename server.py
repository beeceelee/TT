from flask import Flask
import threading
from bot import run_bot

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running on Render!"

if __name__ == "__main__":
    # Run Telegram bot in a separate thread
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=10000)
