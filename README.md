# Ezward AI Telegram Bot

AI assistant hỗ trợ công việc AIQuinta/Anduin, dịch thuật, tóm tắt tài liệu. Hỗ trợ **2 AI providers**: Groq (nhanh) + Google Gemini (mạnh).

## Setup

### 1. Lấy API Keys

#### Groq API Key
- Vào https://console.groq.com → Sign in
- Tạo API key → Copy

#### Google AI Studio API Key
- Vào https://aistudio.google.com → Sign in bằng Google
- Bấm **Get API Key** → **Create API Key**
- Copy key

### 2. Environment Variables (set trên Railway)
```
TELEGRAM_TOKEN=your_telegram_bot_token
GROQ_API_KEY=your_groq_api_key
GOOGLE_API_KEY=your_google_ai_studio_key
```

### 3. Deploy Railway

1. Push code lên GitHub
2. Vào railway.app → New Project → Deploy from GitHub
3. Set 3 environment variables ở trên
4. Done!

## Commands

- `/start` - Chào mừng + hiển thị AI provider đang dùng
- `/use_groq` - Chuyển sang **Groq Llama 3.3 70B** (⚡ nhanh nhất)
- `/use_gemini` - Chuyển sang **Google Gemini 2.5 Flash** (🧠 mạnh nhất)
- `/translate [text]` - Dịch Anh-Việt
- `/summarize [text]` - Tóm tắt văn bản
- `/clear` - Xóa lịch sử chat

## So sánh 2 AI Provider

| Tiêu chí | Groq | Gemini |
|---------|------|--------|
| **Tốc độ** | ⚡⚡⚡ Cực nhanh | ⚡⚡ Nhanh |
| **Chính xác** | 🎯 Tốt | 🎯🎯🎯 Xuất sắc |
| **Context** | 32K token | 1M token |
| **Use case** | Chat realtime, dịch thuật | Dài hạn, phân tích phức tạp |

## Default Behavior
- Bot mặc định dùng **Groq** (nhanh)
- Bạn có thể switch sang Gemini bất kỳ lúc nào với `/use_gemini`

## Lịch sử chat
Bot lưu tối đa 20 tin nhắn gần nhất per user, giúp context liên tục.
