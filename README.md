# 🤖 Telegram Shaxsiy AI Yordamchi (24/7 Tekin Serverlar Uchun)

Ushbu loyiha sizning Telegramdagi shaxsiy yordamchingiz bo'lib, quyidagi vazifalarni **maksimal tezlikda** bajaradi:

1. **Online / Offline aqlli tekshiruv**: Agar siz Telegramda **online** bo'lsangiz (yoki o'zingiz yozayotgan bo'lsangiz), AI umuman aralashmaydi va javob bermaydi.
2. **Ming yillik qadrdondek suhbat**: Agar siz **offline** bo'lsangiz, sizga yozgan insonlarga bitta quruq gap qaytarmasdan, chatdagi oldingi suhbat tarixini o'qib, xuddi ming yillik qadrdon do'stdek samimiy suhbatlashadi.
3. **Har doim kitobdan iqtibos**: Har bir javobda suhbat mavzusiga mos keladigan mashhur kitoblardan (o'zbek va jahon adabiyotidan) chiroyli iqtibos va muallifini keltiradi.
4. **2 ta tugmali Boshqaruv Boti**: Maxsus Telegram botingizda faqat 2 ta tugma bo'ladi:
   - `🟢 Yordamchini ishga tushirish` — AI yordamchini yoqadi.
   - `🔴 Yordamchini ishini to'xtatish` — AI yordamchini darhol to'xtatadi.
5. **24/7 Tekin Serverda Ishlash**: Ichiga o'rnatilgan `/health` web-serveri orqali Render.com, Koyeb yoki HuggingFace Spaces kabi bepul serverlarda 24/7 to'xtovsiz ishlaydi.

---

## 🛠️ 1-QADAM: Kerakli kalitlarni olish (Barchasi BEPUL)

Loyiha papkasidagi `.env` faylini ochib, quyidagi ma'lumotlarni kiriting:

1. **`API_ID` va `API_HASH`**:
   - [https://my.telegram.org](https://my.telegram.org) saytiga telefon raqamingiz bilan kiring.
   - **API development tools** bo'limiga o'ting va dastur yaratib `api_id` hamda `api_hash` ni nusxalab oling.
2. **`BOT_TOKEN`** (2 ta tugmali boshqaruv boti uchun):
   - Telegramda [@BotFather](https://t.me/BotFather) ga kiring, `/newbot` deb yozib yangi bot oching va berilgan Tokenni `.env` fayliga joylang.
3. **`GROQ_API_KEY`** (Maksimal tezlikdagi bepul AI uchun):
   - [https://console.groq.com/keys](https://console.groq.com/keys) saytidan ro'yxatdan o'tib, bepul API kalit oling (soniyasiga 500+ so'z tezlikda ishlaydi!).
   - *(Ixtiyoriy)* Yoki [Google AI Studio](https://aistudio.google.com/app/apikey) dan bepul `GEMINI_API_KEY` olishingiz mumkin.

---

## 💻 2-QADAM: Sessiya kodini olish va Kompyuterda ishga tushirish

1. Terminal (yoki CMD) ochib, avval shaxsiy profilingiz uchun `SESSION_STRING` oling:
   ```bash
   python generate_session.py
   ```
   *(Telefon raqamingiz va Telegramga kelgan kodni kiritasiz — u avtomatik `.env` fayliga `SESSION_STRING` ni saqlaydi).*

2. Loyihani ishga tushirish uchun **`start.bat`** faylini ikki marta bosing (yoki `python main.py` buyrug'ini bering).

---

## ☁️ 3-QADAM: 24/7 Tekin Serverga Joylash (Kompyuter o'chiq bo'lganda ham ishlashi uchun)

Loyiha 24/7 bepul ishlashi uchun **Render.com** + **cron-job.org** (yoki **UptimeRobot**) dan foydalanamiz:

1. Ushbu papkadagi fayllarni o'zingizning **GitHub** (Private/Yopiq) repozitoriyangizga yuklang (`.env` fayli yuklanmaydi, `.gitignore` uni himoyalaydi).
2. [https://render.com](https://render.com) saytida bepul akkaunt oching va **New + -> Web Service** ni bosing.
3. GitHub repozitoriyangizni ulang:
   - **Runtime**: `Python 3` (yoki `Docker`)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Instance Type**: `Free` ($0 / oy)
4. **Environment Variables** bo'limiga `.env` ichidagi qiymatlarni kiriting:
   - `API_ID`
   - `API_HASH`
   - `SESSION_STRING`
   - `BOT_TOKEN`
   - `GROQ_API_KEY`
   - `OWNER_NAME`
5. Server ishga tushgach, Render sizga `https://sizning-loyihangiz.onrender.com` ko'rinishida havola beradi.
6. **Uxlab qolmasligi uchun (24/7 Keep-Alive)**:
   - [https://cron-job.org](https://cron-job.org) yoki [https://uptimerobot.com](https://uptimerobot.com) bepul saytiga kiring.
   - Har **5 daqiqada** `https://sizning-loyihangiz.onrender.com/health` manziliga kirib turadigan monitor yoqing.
   - Shu bilan serveringiz yiliga 365 kun, sutkasiga **24/7 mutlaqo tekin** va to'xtovsiz ishlaydi!
