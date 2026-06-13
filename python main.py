import os
import telebot
from flask import Flask, request
from openai import OpenAI

# 1. Fetch Environment Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")

# Render automatically provides this environment variable to web services
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL") 

# Check if tokens are present
if not BOT_TOKEN or not HF_TOKEN:
    raise ValueError("BOT_TOKEN or HF_TOKEN is missing in environment variables.")

# 2. Initialize Telegram Bot and Flask App
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# 3. Initialize OpenAI Client (Pointed to Hugging Face router)
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

# 4. Handle incoming Telegram messages
@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    try:
        # Show "typing..." status to the user
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Call Hugging Face API using the OpenAI SDK format
        chat_completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V4-Pro:novita",
            messages=[
                {
                    "role": "user",
                    "content": message.text,
                },
            ],
        )
        
        # Extract the AI's reply and send it back to Telegram
        ai_reply = chat_completion.choices[0].message.content
        bot.reply_to(message, ai_reply)
        
    except Exception as e:
        bot.reply_to(message, f"Sorry, an error occurred: {str(e)}")

# 5. Flask Route to receive Webhook from Telegram
@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    # Process the incoming JSON updates from Telegram
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

# 6. Flask Route for Health Check (Render needs this to know the app is awake)
@app.route('/')
def index():
    return "Telegram Bot is running smoothly on Render!", 200

# 7. Set Webhook automatically when the app starts
if RENDER_EXTERNAL_URL:
    # Telegram sends updates to https://<your-render-url>/<BOT_TOKEN>
    webhook_url = f"{RENDER_EXTERNAL_URL}/{BOT_TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)

# Run the app (Only used if testing locally. Render uses Gunicorn)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
