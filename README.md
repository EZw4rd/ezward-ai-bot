# Ezward AI Telegram Bot

Simple Telegram bot powered by Groq API (Llama 3.1 70B).

## Features
- 💬 Chat with AI
- 🌐 Translate EN ↔ VN
- 📄 Summarize documents
- 💾 Chat history per user (last 10 messages)

## Setup

### 1. Get API Keys

**Telegram Bot Token:**
- Open Telegram → Search @BotFather
- `/newbot` → name your bot → copy token

**Groq API Key:**
- Visit https://console.groq.com
- Sign in → Create API key → Copy

### 2. Deploy on Railway

1. Push code to GitHub
2. railway.app → New Project → Deploy from GitHub
3. Set env variables:
   - `TELEGRAM_TOKEN` = your bot token
   - `GROQ_API_KEY` = your Groq key
4. Done! Bot runs 24/7

## Commands
- `/start` - Welcome
- `/translate [text]` - Translate
- `/summarize [text]` - Summarize
- `/clear` - Clear chat history
- Or just chat normally

## Model
- **Model**: Llama 3.1 70B (Groq)
- **Speed**: Ultra-fast (sub-second responses)
- **Cost**: Free tier generous

## Notes
- Bot stores last 10 messages per user
- Max response: 1024 tokens
- Telegram limit: 4096 chars per message
