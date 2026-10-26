import logging
import aiohttp
from typing import List, Dict, Optional
from config import (
    GROQ_API_KEY,
    GEMINI_API_KEY,
    GROQ_MODEL,
    GEMINI_MODEL,
    OWNER_NAME,
)

logger = logging.getLogger("AIEngine")

SYSTEM_PROMPT = f"""Sen "{OWNER_NAME}"ning shaxsiy Telegram profilidagi eng yaqin yordamchisi va uning nomidan (yoki uning eng yaqin ishonchli vakili/o'zi kabi) javob beruvchi aqlli suhbatdoshsan.
Hozir {OWNER_NAME} offline (band yoki tarmoqda emas), shuning uchun suhbatdoshni yolg'izlatib qo'ymaslik uchun sen u bilan suhbatlashyapsan.

MUHIM QOIDALAR (Bularga 100% amal qil!):
1. MING YILLIK QADRDONDEK MUOMALA: Suhbatdosh bilan xuddi ming yillik qadrdon do'stdek, juda samimiy, iliq, hurmat bilan va jonli gaplash. Robotga o'xshab quruq yoki rasmiy gapirma!
2. FAQAT BITTA GAP QAYTARMA: "Hozir bandman, keyin yozaman" deb bitta quruq gap bilan cheklanib qolma! Suhbatdosh nima haqida yozayotgan bo'lsa, chatdagi oldingi xabarlar tarixiga qarab, mavzuni davom ettir, hol-ahvol so'ra, fikr bildir, savoliga to'liq va qiziqarli javob ber.
3. HAR DOIM KITOBDAN IQTIBOS KELTIR: Har bir javobingda suhbat mavzusiga, insonning kayfiyatiga yoki vaziyatga mos keladigan biror mashhur kitobdan (o'zbek yoki jahon adabiyoti durdonalaridan — masalan, O'tkir Hoshimov, Abdulla Qodiriy, Cho'lpon, Chingiz Aytmatov, Antuan de Sent-Ekzyuperi, Paulo Koelo, Deyl Karnegi, Rumiy, Navoiy va boshqalar) ta'sirli iqtibos keltir va qaysi kitob/muallif ekanini chiroyli qilib yozib o't (masalan: 📚 *"..."* — Kitob nomi / Muallif).
4. TIL VA USLUB: Suhbatdosh qaysi tilda (o'zbek, rus, ingliz) yozsa, o'sha tilda javob ber (asosiy til — samimiy o'zbek tili). Xabarlaring o'qishga qulay, tabiiy va 3-6 gap atrofida bo'lsin.
"""


class AIEngine:
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=20)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def generate_reply(
        self,
        sender_name: str,
        chat_history: List[Dict[str, str]],
    ) -> str:
        """
        Chat tarixiga asoslanib maksimal tezlikda javob qaytaradi.
        Avval Groq (eng tez), so'ng Gemini orqali urinib ko'radi.
        """
        context_prompt = (
            f"Suhbatdoshning ismi: {sender_name}.\n"
            f"Quyida chatdagi oxirgi yozishmalar keltirilgan. Suhbatdoshning oxirgi xabarlariga "
            f"ming yillik qadrdondek samimiy javob ber va mavzuga mos kitobdan iqtibos qo'sh."
        )

        if GROQ_API_KEY:
            try:
                return await self._call_groq(context_prompt, chat_history)
            except Exception as e:
                logger.error(f"Groq xatoligi: {e}")

        if GEMINI_API_KEY:
            try:
                return await self._call_gemini(context_prompt, chat_history)
            except Exception as e:
                logger.error(f"Gemini xatoligi: {e}")

        # Agar API kalitlar hali kiritilmagan yoki xato bo'lsa, zaxira javob
        return (
            f"Assalomu alaykum, qadrdonim {sender_name}! Qalaysiz, ishlaringiz va kayfiyatingiz a'lomi? 😊 "
            f"Hozirgina tarmoqdan biroz uzoqroqda edim, lekin sizdek yaqin insonimning xabarini javobsiz qoldirgim kelmadi. "
            f"Yozganlaringizni albatta diqqat bilan o'qib chiqaman, bemalol fikrlaringizni yozavering!\n\n"
            f"📚 *«Eng katta boylik — bu insoniy muloqot quvonchidir.»* — Antuan de Sent-Ekzyuperi, «Kichkina shahzoda»"
        )

    async def _call_groq(
        self, context_prompt: str, chat_history: List[Dict[str, str]]
    ) -> str:
        session = await self.get_session()
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT + "\n\n" + context_prompt},
            *chat_history,
        ]
        payload = {
            "model": GROQ_MODEL,
            "messages": messages,
            "temperature": 0.75,
            "max_tokens": 500,
        }
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise RuntimeError(f"Groq API status {resp.status}: {text}")
            data = await resp.json()
            return data["choices"][0]["message"]["content"].strip()

    async def _call_gemini(
        self, context_prompt: str, chat_history: List[Dict[str, str]]
    ) -> str:
        session = await self.get_session()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
        contents = []
        for msg in chat_history:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        payload = {
            "system_instruction": {
                "parts": [{"text": SYSTEM_PROMPT + "\n\n" + context_prompt}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": 0.75,
                "maxOutputTokens": 500,
            },
        }
        async with session.post(url, json=payload) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise RuntimeError(f"Gemini API status {resp.status}: {text}")
            data = await resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
