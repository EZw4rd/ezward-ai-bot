#!/usr/bin/env python3
import os
import sys
import logging
import json
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
except ImportError as e:
    logger.error(f"Import error: {e}")
    sys.exit(1)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_TOKEN not set")
    sys.exit(1)
if not GROQ_API_KEY:
    logger.error("GROQ_API_KEY not set")
    sys.exit(1)

logger.info("Environment variables loaded")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """You are a helpful AI assistant for Ezward.
Work with AIQuinta (manufacturing AI) and Anduin Transactions (B2B fintech).
Help with work tasks, translations, and summaries. Respond in user's language."""

user_conversations = {}

def get_user_history(user_id: int) -> list:
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    return user_conversations[user_id]

def add_to_history(user_id: int, role: str, content: str):
    history = get_user_history(user_id)
    history.append({"role": role, "content": content})
    if len(history) > 10:
        user_conversations[user_id] = history[-10:]

async def call_groq(user_id: int, user_message: str, use_history: bool = True) -> str:
    try:
        if use_history:
            add_to_history(user_id, "user", user_message)
            messages = get_user_history(user_id)
        else:
            messages = [{"role": "user", "content": user_message}]

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "llama-3.1-70b-versatile",
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            "max_tokens": 1024,
            "temperature": 0.7
        }

        response = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        reply = data["choices"][0]["message"]["content"]

        if use_history:
            add_to_history(user_id, "assistant", reply)

        return reply

    except Exception as e:
        logger.error(f"Groq error: {e}")
        return f"Error: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi Ezward!\n\n"
        "Commands:\n"
        "/translate [text] - Translate\n"
        "/summarize [text] - Summarize\n"
        "/clear - Clear history\n\n"
        "Or chat normally!"
    )

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_conversations[user_id] = []
    await update.message.reply_text("History cleared")

async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /translate [text]")
        return
    text = " ".join(context.args)
    prompt = f"Translate to other language. Only translation:\n\n{text}"
    await update.message.chat_action("typing")
    response = await call_groq(user_id, prompt, use_history=False)
    await update.message.reply_text(response)

async def summarize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /summarize [text]")
        return
    text = " ".join(context.args)
    prompt = f"Summarize:\n\n{text}"
    await update.message.chat_action("typing")
    response = await call_groq(user_id, prompt, use_history=False)
    await update.message.reply_text(response)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    await update.message.chat_action("typing")
    response = await call_groq(user_id, user_message, use_history=True)
    if len(response) > 4096:
        for i in range(0, len(response), 4096):
            await update.message.reply_text(response[i:i+4096])
    else:
        await update.message.reply_text(response)

def main():
    logger.info("Starting bot...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("translate", translate))
    app.add_handler(CommandHandler("summarize", summarize))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot running...")
    app.run_polling(allowed_updates=['message'])

if __name__ == "__main__":
    main()
