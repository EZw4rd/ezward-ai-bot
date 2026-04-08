#!/usr/bin/env python3
"""
Ezward AI Telegram Bot
- Groq API for fast LLM responses
- Simple polling mode
- No fancy features, just works
"""

import os
import sys
import logging
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    from groq import Groq
except ImportError as e:
    logger.error(f"Import error: {e}")
    sys.exit(1)

# ============================================================================
# CONFIG
# ============================================================================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_TOKEN not set")
    sys.exit(1)
if not GROQ_API_KEY:
    logger.error("GROQ_API_KEY not set")
    sys.exit(1)

logger.info("Environment variables loaded")

# Initialize Groq client (minimal config, no proxies)
try:
    groq_client = Groq(api_key=GROQ_API_KEY)
    logger.info("Groq client initialized")
except Exception as e:
    logger.error(f"Groq init failed: {e}")
    sys.exit(1)

# ============================================================================
# SYSTEM PROMPT
# ============================================================================

SYSTEM_PROMPT = """You are a helpful AI assistant for Ezward.

You work with:
- AIQuinta: AI company focused on manufacturing (products: AIQ, DxF)
- Anduin Transactions: B2B fintech platform for private markets

Your tasks:
1. Help with work-related tasks
2. Translate English ↔ Vietnamese
3. Summarize documents

Always respond in the language the user uses (English or Vietnamese).
Be professional but friendly."""

# ============================================================================
# IN-MEMORY STORAGE
# ============================================================================

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

# ============================================================================
# GROQ CALLS
# ============================================================================

async def call_groq(user_id: int, user_message: str, use_history: bool = True) -> Optional[str]:
    try:
        if use_history:
            add_to_history(user_id, "user", user_message)
            messages = get_user_history(user_id)
        else:
            messages = [{"role": "user", "content": user_message}]

        response = groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            max_tokens=1024,
            temperature=0.7
        )

        reply = response.choices[0].message.content

        if use_history:
            add_to_history(user_id, "assistant", reply)

        return reply

    except Exception as e:
        logger.error(f"Groq call failed: {e}")
        return f"Error: {str(e)}"

# ============================================================================
# HANDLERS
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi Ezward! I'm your AI assistant.\n\n"
        "I can help with:\n"
        "• Work tasks (AIQuinta/Anduin)\n"
        "• Translation (EN ↔ VN)\n"
        "• Document summarization\n\n"
        "Commands:\n"
        "/translate [text]\n"
        "/summarize [text]\n"
        "/clear\n\n"
        "Or just chat! 💬"
    )

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_conversations[user_id] = []
    await update.message.reply_text("Chat history cleared")

async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text("Usage: /translate [text]")
        return

    text = " ".join(context.args)
    prompt = f"Translate to the other language. Only return translation:\n\n{text}"
    
    await update.message.chat_action("typing")
    response = await call_groq(user_id, prompt, use_history=False)
    await update.message.reply_text(response if response else "Error")

async def summarize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text("Usage: /summarize [text]")
        return

    text = " ".join(context.args)
    prompt = f"Summarize concisely:\n\n{text}"
    
    await update.message.chat_action("typing")
    response = await call_groq(user_id, prompt, use_history=False)
    await update.message.reply_text(response if response else "Error")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    
    await update.message.chat_action("typing")
    response = await call_groq(user_id, user_message, use_history=True)
    
    if response:
        if len(response) > 4096:
            for i in range(0, len(response), 4096):
                await update.message.reply_text(response[i:i+4096])
        else:
            await update.message.reply_text(response)

# ============================================================================
# MAIN
# ============================================================================

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
