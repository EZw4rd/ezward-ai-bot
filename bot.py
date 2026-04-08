import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq
import google.generativeai as genai

# Logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Clients
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
gemini_model = genai.GenerativeModel("gemini-2.5-flash")

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]

# Track AI provider per user (default: groq)
user_providers = {}

SYSTEM_PROMPT = """Bạn là một AI assistant chuyên nghiệp hỗ trợ công việc cho Ezward - người làm việc tại AIQuinta và Anduin Transactions.

AIQuinta: công ty AI tập trung vào manufacturing sector, có 2 sản phẩm là AIQ và DxF.
Anduin Transactions: nền tảng B2B fintech cho private markets / LP management.

Nhiệm vụ chính của bạn:
1. Hỗ trợ công việc: soạn thảo, brainstorm, phân tích cho AIQuinta và Anduin
2. Dịch thuật Anh-Việt và Việt-Anh chính xác, tự nhiên
3. Tóm tắt văn bản, tài liệu một cách súc tích

Phong cách: chuyên nghiệp nhưng thân thiện, trả lời bằng ngôn ngữ người dùng dùng (Việt hoặc Anh).
Nếu người dùng paste văn bản dài → tự động tóm tắt hoặc hỏi họ muốn làm gì với đoạn văn đó."""

# Lưu lịch sử chat theo user
conversation_history = {}

def get_history(user_id):
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    return conversation_history[user_id]

def add_message(user_id, role, content):
    history = get_history(user_id)
    history.append({"role": role, "content": content})
    # Giữ tối đa 20 tin nhắn gần nhất
    if len(history) > 20:
        conversation_history[user_id] = history[-20:]

def get_provider(user_id):
    """Get current AI provider for user (default: groq)"""
    return user_providers.get(user_id, "groq")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    provider = get_provider(update.effective_user.id)
    await update.message.reply_text(
        "👋 Chào Ezward! Mình là AI assistant của bạn.\n\n"
        f"🤖 Đang dùng: **{provider.upper()}**\n\n"
        "Mình có thể giúp:\n"
        "• 💼 Công việc AIQuinta / Anduin\n"
        "• 🌐 Dịch thuật Anh ↔ Việt\n"
        "• 📄 Tóm tắt văn bản / tài liệu\n\n"
        "Commands:\n"
        "/translate [text] — Dịch văn bản\n"
        "/summarize [text] — Tóm tắt\n"
        "/use_groq — Dùng Groq (nhanh nhất)\n"
        "/use_gemini — Dùng Google Gemini (mạnh nhất)\n"
        "/clear — Xóa lịch sử chat\n\n"
        "Hoặc chat bình thường là được! 💬"
    )

async def use_groq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_providers[user_id] = "groq"
    await update.message.reply_text("✅ Chuyển sang **Groq Llama 3.3 70B** (nhanh nhất)\n⚡ Tốc độ tối ưu cho chat realtime")

async def use_gemini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_providers[user_id] = "gemini"
    await update.message.reply_text("✅ Chuyển sang **Google Gemini 2.5 Flash** (mạnh nhất)\n🧠 Độ chính xác cao hơn, context lớn hơn")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_history[user_id] = []
    await update.message.reply_text("✅ Đã xóa lịch sử chat!")

async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Usage: /translate [nội dung cần dịch]")
        return
    
    prompt = f"Dịch đoạn văn sau sang ngôn ngữ còn lại (nếu là tiếng Việt thì dịch sang Anh, nếu là tiếng Anh thì dịch sang Việt). Chỉ trả về bản dịch, không giải thích:\n\n{text}"
    response = await call_ai(user_id, prompt, use_history=False)
    await update.message.reply_text(f"🌐 *Bản dịch:*\n\n{response}", parse_mode="Markdown")

async def summarize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Usage: /summarize [nội dung cần tóm tắt]")
        return
    
    prompt = f"Tóm tắt đoạn văn sau một cách súc tích, giữ lại các ý chính quan trọng:\n\n{text}"
    response = await call_ai(user_id, prompt, use_history=False)
    await update.message.reply_text(f"📄 *Tóm tắt:*\n\n{response}", parse_mode="Markdown")

async def call_ai(user_id, user_message, use_history=True):
    """Call AI based on user's selected provider"""
    provider = get_provider(user_id)
    
    try:
        if provider == "gemini":
            return await call_gemini(user_id, user_message, use_history)
        else:  # default to groq
            return await call_groq(user_id, user_message, use_history)
    except Exception as e:
        logger.error(f"AI error ({provider}): {e}")
        return f"❌ Lỗi: {str(e)}"

async def call_groq(user_id, user_message, use_history=True):
    """Call Groq API (Llama 3.3 70B)"""
    try:
        if use_history:
            add_message(user_id, "user", user_message)
            messages = get_history(user_id)
        else:
            messages = [{"role": "user", "content": user_message}]

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            max_tokens=2048,
            temperature=0.7,
        )
        
        reply = response.choices[0].message.content
        
        if use_history:
            add_message(user_id, "assistant", reply)
        
        return reply
    except Exception as e:
        logger.error(f"Groq error: {e}")
        raise

async def call_gemini(user_id, user_message, use_history=True):
    """Call Google Gemini 2.5 Flash API"""
    try:
        if use_history:
            add_message(user_id, "user", user_message)
            messages = get_history(user_id)
            # Convert to Gemini format
            chat = gemini_model.start_chat(history=[
                {"role": "model" if m["role"] == "assistant" else "user", 
                 "parts": [{"text": m["content"]}]}
                for m in messages[:-1]  # Exclude the last user message we just added
            ])
            response = chat.send_message(
                f"{SYSTEM_PROMPT}\n\nUser: {user_message}",
                generation_config={"max_output_tokens": 2048, "temperature": 0.7}
            )
        else:
            response = gemini_model.generate_content(
                f"{SYSTEM_PROMPT}\n\nUser: {user_message}",
                generation_config={"max_output_tokens": 2048, "temperature": 0.7}
            )
        
        reply = response.text
        
        if use_history:
            add_message(user_id, "assistant", reply)
        
        return reply
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        raise

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # Gửi "typing..."
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    reply = await call_ai(user_id, user_message)
    
    # Telegram giới hạn 4096 ký tự
    if len(reply) > 4096:
        for i in range(0, len(reply), 4096):
            await update.message.reply_text(reply[i:i+4096])
    else:
        await update.message.reply_text(reply)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("translate", translate))
    app.add_handler(CommandHandler("summarize", summarize))
    app.add_handler(CommandHandler("use_groq", use_groq))
    app.add_handler(CommandHandler("use_gemini", use_gemini))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Bot started! Providers available: Groq, Gemini")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
