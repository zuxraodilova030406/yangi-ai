import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Userbot (Shaxsiy profil uchun - my.telegram.org dan olinadi)
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "").strip()
SESSION_STRING = os.getenv("SESSION_STRING", "").strip()

# Boshqaruv Boti (@BotFather dan olinadi)
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# AI API Kalitlari (Groq yoki Gemini - ikkalasidan biri yetarli, Groq eng tezi!)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# AI Model sozlamalari
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Qo'shimcha sozlamalar
OWNER_NAME = os.getenv("OWNER_NAME", "Do'stingiz")
PORT = int(os.getenv("PORT", "8080"))
# Yozishdan oldin necha soniya kutish (ketma-ket kelgan xabarlarni bitta qilib o'qish uchun)
DEBOUNCE_SECONDS = float(os.getenv("DEBOUNCE_SECONDS", "1.5"))
