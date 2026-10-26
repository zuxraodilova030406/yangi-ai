import os
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv, set_key

load_dotenv()

print("=" * 60)
print("🔐 TELEGRAM SHAXSIY PROFIL UCHUN SESSION_STRING OLISH")
print("=" * 60)

api_id = os.getenv("API_ID", "").strip()
api_hash = os.getenv("API_HASH", "").strip()

if not api_id or api_id == "0":
    api_id = input("1. API_ID ni kiriting (my.telegram.org saytidan): ").strip()

if not api_hash:
    api_hash = input("2. API_HASH ni kiriting (my.telegram.org saytidan): ").strip()

with TelegramClient(StringSession(), int(api_id), api_hash) as client:
    session_str = client.session.save()
    print("\n✅ MUVAFFAQIYATLI ULANDI!")
    print("\nSizning SESSION_STRING kodingiz (buni hech kimga bermang!):\n")
    print(session_str)
    print("\n" + "=" * 60)

    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        set_key(env_path, "API_ID", str(api_id))
        set_key(env_path, "API_HASH", api_hash)
        set_key(env_path, "SESSION_STRING", session_str)
        print("✅ SESSION_STRING avtomatik ravishda .env fayliga saqlandi!")
    else:
        print("Yuqoridagi SESSION_STRING kodini .env fayliga yoki serveringizga joylang.")
