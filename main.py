import asyncio
import json
import logging
import os
import time
from typing import Dict, Set

from aiohttp import web
from telethon import TelegramClient, events, functions, types, Button
from telethon.sessions import StringSession

from config import (
    API_ID,
    API_HASH,
    SESSION_STRING,
    BOT_TOKEN,
    PORT,
    DEBOUNCE_SECONDS,
)
from ai_engine import AIEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("TelegramAIAssistant")

STATE_FILE = os.path.join(os.path.dirname(__file__), "state.json")

# Tugmalar matni (Aniq talab bo'yicha 2 ta tugma)
BTN_START = "🟢 Yordamchini ishga tushirish"
BTN_STOP = "🔴 Yordamchini ishini to'xtatish"


class AssistantState:
    def __init__(self):
        self.enabled: bool = True
        self.owner_id: int = 0
        self.last_manual_activity: float = 0.0
        self.ai_sent_message_ids: Set[int] = set()
        self.load()

    def load(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.enabled = data.get("enabled", True)
                    self.owner_id = data.get("owner_id", 0)
            except Exception as e:
                logger.warning(f"Holat faylini o'qishda xatolik: {e}")

    def save(self):
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(
                    {"enabled": self.enabled, "owner_id": self.owner_id},
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as e:
            logger.warning(f"Holat faylini saqlashda xatolik: {e}")


state = AssistantState()
ai_engine = AIEngine()
pending_tasks: Dict[int, asyncio.Task] = {}


async def is_owner_online(user_client: TelegramClient) -> bool:
    """
    Foydalanuvchi (akkaunt egasi) hozir online yoki yo'qligini tekshiradi.
    Agar foydalanuvchi online bo'lsa yoki oxirgi 45 soniya ichida o'zi qo'lda yozgan bo'lsa -> True qaytaradi.
    """
    # Agar egasi hozirgina o'zi qo'lda xabar yozgan bo'lsa, u online hisoblanadi
    if time.time() - state.last_manual_activity < 45:
        return True

    try:
        me = await user_client.get_me()
        if isinstance(me.status, types.UserStatusOnline):
            return True
    except Exception as e:
        logger.warning(f"Online statusni tekshirishda xatolik: {e}")

    return False


async def fetch_chat_context(
    client: TelegramClient, chat_id: int, limit: int = 12
) -> list:
    """
    Chatdagi oxirgi yozishmalarni o'qib, AI suhbatni davom ettirishi uchun kontekst hosil qiladi.
    """
    history = []
    try:
        messages = await client.get_messages(chat_id, limit=limit)
        for msg in reversed(messages):
            text = (msg.message or "").strip()
            if not text:
                continue
            role = "assistant" if msg.out else "user"
            history.append({"role": role, "content": text})
    except Exception as e:
        logger.error(f"Chat tarixini olishda xatolik: {e}")
    return history


async def handle_debounced_reply(
    user_client: TelegramClient, chat_id: int, sender_name: str
):
    """
    Suhbatdosh ketma-ket 2-3 ta xabar yozganda barchasini kutib,
    online emasligini tekshirib, bitta mukammal javob qaytaradi.
    """
    try:
        await asyncio.sleep(DEBOUNCE_SECONDS)

        # 1. Yordamchi yoqilganligini tekshirish
        if not state.enabled:
            logger.info(f"Yordamchi o'chiq. {sender_name} ga javob berilmadi.")
            return

        # 2. Akkaunt egasi ONLINE ekanligini tekshirish
        if await is_owner_online(user_client):
            logger.info(f"Akkaunt egasi ONLINE! {sender_name} ga javob berilmadi.")
            return

        # 3. Chat tarixini o'qish
        chat_history = await fetch_chat_context(user_client, chat_id, limit=12)
        if not chat_history or chat_history[-1]["role"] == "assistant":
            return

        # 4. Yozayotganlik ("typing...") effektini ko'rsatish va AI javobini olish
        async with user_client.action(chat_id, "typing"):
            reply_text = await ai_engine.generate_reply(
                sender_name=sender_name,
                chat_history=chat_history,
            )

        # Yuborishdan oldin yana bir bor online bo'lib qolmaganini tekshiramiz
        if not state.enabled or await is_owner_online(user_client):
            return

        sent_msg = await user_client.send_message(chat_id, reply_text)
        state.ai_sent_message_ids.add(sent_msg.id)
        if len(state.ai_sent_message_ids) > 500:
            state.ai_sent_message_ids.clear()

        # Akkauntni sun'iy ravishda "online" bo'lib qolmasligi uchun offline statusni saqlaymiz
        try:
            await user_client(functions.account.UpdateStatusRequest(offline=True))
        except Exception:
            pass

        logger.info(f"✅ {sender_name} ({chat_id}) ga AI javob qaytardi.")

    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Javob qaytarishda xatolik ({chat_id}): {e}")
    finally:
        pending_tasks.pop(chat_id, None)


def setup_userbot_handlers(user_client: TelegramClient):
    """
    Shaxsiy akkauntga kelgan xabarlarni kuzatuvchi handlerlar.
    """

    @user_client.on(events.NewMessage(outgoing=True))
    async def on_owner_manual_message(event: events.NewMessage.Event):
        # Agar bu xabarni AI emas, egasining o'zi yozgan bo'lsa -> demak egasi online!
        if event.id not in state.ai_sent_message_ids:
            state.last_manual_activity = time.time()
            # Shu chatda kutilayotgan AI javobi bo'lsa bekor qilamiz
            task = pending_tasks.pop(event.chat_id, None)
            if task and not task.done():
                task.cancel()

    @user_client.on(events.NewMessage(incoming=True))
    async def on_incoming_private_message(event: events.NewMessage.Event):
        # Faqat shaxsiy (private) yozishmalarga javob beramiz (guruh va kanallarga emas)
        if not event.is_private:
            return

        sender = await event.get_sender()
        if not sender or getattr(sender, "bot", False) or getattr(sender, "is_self", False):
            return

        # Telegram rasmiy xizmat xabarlarini o'tkazib yuboramiz (777000)
        if sender.id == 777000:
            return

        if not state.enabled:
            return

        if await is_owner_online(user_client):
            logger.info("Foydalanuvchi online — AI javob bermaydi.")
            return

        sender_name = (
            f"{getattr(sender, 'first_name', '') or ''} {getattr(sender, 'last_name', '') or ''}"
        ).strip() or "Qadrdonim"

        # Agar shu inson ketma-ket yozayotgan bo'lsa, oldingi taymerni yangilaymiz
        old_task = pending_tasks.get(event.chat_id)
        if old_task and not old_task.done():
            old_task.cancel()

        pending_tasks[event.chat_id] = asyncio.create_task(
            handle_debounced_reply(user_client, event.chat_id, sender_name)
        )


def get_control_keyboard():
    """
    Telegram botdagi 2 ta asosiy tugma (Reply Keyboard).
    """
    return [
        [Button.text(BTN_START, resize=True)],
        [Button.text(BTN_STOP, resize=True)],
    ]


def get_inline_control_keyboard():
    """
    Xabar ostida ham chiqadigan 2 ta Inline tugma.
    """
    return [
        [Button.inline(BTN_START, data=b"start_ai")],
        [Button.inline(BTN_STOP, data=b"stop_ai")],
    ]


def setup_bot_handlers(bot_client: TelegramClient):
    """
    Telegram Boshqaruv Boti (2 ta tugma orqali yordamchini yoqish va o'chirish).
    """

    @bot_client.on(events.NewMessage(pattern=r"^/start"))
    async def on_bot_start(event: events.NewMessage.Event):
        if state.owner_id == 0:
            state.owner_id = event.sender_id
            state.save()

        status_text = "🟢 ISHLAMOQDA (Yoqilgan)" if state.enabled else "🔴 TO'XTATILGAN (O'chiq)"
        msg = (
            f"🤖 **Shaxsiy AI Yordamchi Boshqaruv Paneli**\n\n"
            f"📊 Hozirgi holat: **{status_text}**\n\n"
            f"• Agar **«{BTN_START}»** tugmasini bossangiz — siz offline bo'lganingizda "
            f"sizga yozgan insonlar bilan ming yillik qadrdondek suhbatlashaman va mavzuga mos kitoblardan iqtibos keltiraman.\n"
            f"• Agar siz **online** bo'lsangiz — suhbatingizga xalaqit bermayman.\n"
            f"• Agar **«{BTN_STOP}»** tugmasini bossangiz — AI o'z ishini darhol to'xtatadi.\n\n"
            f"👇 Quyidagi 2 ta tugmadan birini tanlang:"
        )
        await event.respond(msg, buttons=get_control_keyboard())

    @bot_client.on(events.NewMessage( func=lambda e: e.raw_text in [BTN_START, BTN_STOP]))
    async def on_button_click(event: events.NewMessage.Event):
        if state.owner_id != 0 and event.sender_id != state.owner_id:
            await event.respond("⛔ Kechirasiz, bu botni faqat uning egasi boshqara oladi.")
            return

        if event.raw_text == BTN_START:
            state.enabled = True
            state.save()
            await event.respond(
                "✅ **Yordamchi ISHGA TUSHIRILDI!**\n\n"
                "Endi siz offline bo'lgan vaqtingizda sizga yozgan insonlarga ming yillik qadrdondek samimiy javob qaytaraman "
                "va har doim suhbat mavzusiga mos kitobdan iqtibos keltiraman. 📚✨",
                buttons=get_control_keyboard(),
            )
            logger.info("🟢 Yordamchi bot orqali ISHGA TUSHIRILDI.")

        elif event.raw_text == BTN_STOP:
            state.enabled = False
            state.save()
            # Kutilayotgan barcha javoblarni to'xtatish
            for task in list(pending_tasks.values()):
                if not task.done():
                    task.cancel()
            pending_tasks.clear()

            await event.respond(
                "🛑 **Yordamchi ishi TO'XTATILDI!**\n\n"
                "Endi hech kimga avtomatik javob qaytarilmaydi. Qayta yoqish uchun «🟢 Yordamchini ishga tushirish» tugmasini bosing.",
                buttons=get_control_keyboard(),
            )
            logger.info("🔴 Yordamchi bot orqali TO'XTATILDI.")

    @bot_client.on(
        events.NewMessage(
            incoming=True,
            func=lambda e: e.is_private
            and e.raw_text not in [BTN_START, BTN_STOP]
            and not (e.raw_text or "").startswith("/"),
        )
    )
    async def on_bot_direct_chat(event: events.NewMessage.Event):
        """
        Botning o'ziga oddiy xabar yozilganda ham (sinab ko'rish yoki bot orqali suhbatlashish uchun)
        yordamchi yoqilgan bo'lsa ming yillik qadrdondek javob beradi.
        """
        if not state.enabled:
            if event.sender_id == state.owner_id or state.owner_id == 0:
                await event.respond(
                    "🔴 Hozir yordamchi to'xtatilgan. Ishga tushirish uchun pastdagi **«🟢 Yordamchini ishga tushirish»** tugmasini bosing.",
                    buttons=get_control_keyboard(),
                )
            return

        sender = await event.get_sender()
        sender_name = (
            f"{getattr(sender, 'first_name', '') or ''} {getattr(sender, 'last_name', '') or ''}"
        ).strip() or "Qadrdonim"

        async with bot_client.action(event.chat_id, "typing"):
            chat_history = await fetch_chat_context(bot_client, event.chat_id, limit=10)
            if not chat_history:
                chat_history = [{"role": "user", "content": event.raw_text}]
            reply_text = await ai_engine.generate_reply(
                sender_name=sender_name,
                chat_history=chat_history,
            )

        await event.respond(reply_text, buttons=get_control_keyboard())

    @bot_client.on(events.CallbackQuery)
    async def on_inline_callback(event: events.CallbackQuery.Event):
        if state.owner_id != 0 and event.sender_id != state.owner_id:
            await event.answer("Faqat bot egasi uchun!", alert=True)
            return

        if event.data == b"start_ai":
            state.enabled = True
            state.save()
            await event.answer("✅ Yordamchi ishga tushirildi!", alert=False)
            await event.edit(
                "✅ **Yordamchi ISHGA TUSHIRILDI!**\nOffline vaqtingizda qadrdon do'stdek javob beraman.",
                buttons=get_inline_control_keyboard(),
            )
        elif event.data == b"stop_ai":
            state.enabled = False
            state.save()
            await event.answer("🛑 Yordamchi to'xtatildi!", alert=False)
            await event.edit(
                "🛑 **Yordamchi ishi TO'XTATILDI!**\nAvtomatik javoblar o'chirildi.",
                buttons=get_inline_control_keyboard(),
            )


async def start_keep_alive_server():
    """
    24/7 tekin serverlarda (Render, Koyeb, HuggingFace, Replit) uxlab qolmasligi uchun
    HTTP Web-server. UptimeRobot yoki cron-job.org orqali har 5 daqiqada ping qilinadi.
    """
    app = web.Application()

    async def handle_root(request):
        status_str = "ISHLAMOQDA (ON)" if state.enabled else "TO'XTATILGAN (OFF)"
        return web.json_response(
            {
                "status": "ok",
                "assistant_state": status_str,
                "uptime": "24/7 Active",
            }
        )

    app.router.add_get("/", handle_root)
    app.router.add_get("/health", handle_root)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"🌐 24/7 Keep-Alive Web Server {PORT}-portda ishga tushdi.")


async def main():
    await start_keep_alive_server()

    if not API_ID or not API_HASH:
        logger.error(
            "⚠️ DIQQAT: .env faylida API_ID va API_HASH kiritilmagan! "
            "Iltimos, .env faylini to'ldiring."
        )
        while True:
            await asyncio.sleep(3600)

    clients = []

    # 1. Shaxsiy akkaunt (Userbot) ulanishi
    if SESSION_STRING:
        user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    else:
        user_client = TelegramClient("shaxsiy_akkaunt_session", API_ID, API_HASH)

    setup_userbot_handlers(user_client)
    await user_client.start()
    me = await user_client.get_me()
    state.owner_id = me.id
    state.save()
    logger.info(f"👤 Shaxsiy profil ulandi: {me.first_name} (ID: {me.id})")
    clients.append(user_client)

    # 2. Boshqaruv Boti (2 ta tugmali Telegram Bot) ulanishi
    if BOT_TOKEN:
        bot_client = TelegramClient("boshqaruv_bot_session", API_ID, API_HASH)
        setup_bot_handlers(bot_client)
        await bot_client.start(bot_token=BOT_TOKEN)
        bot_me = await bot_client.get_me()
        logger.info(f"🤖 Boshqaruv boti ulandi: @{bot_me.username}")
        clients.append(bot_client)
    else:
        logger.warning(
            "⚠️ BOT_TOKEN kiritilmagan! 2 ta tugmali boshqaruv boti ishlashi uchun .env fayliga BOT_TOKEN qo'shing."
        )

    logger.info("🚀 Loyiha maksimal tezlikda 24/7 rejimida ishga tushdi!")
    await asyncio.gather(*(c.run_until_disconnected() for c in clients))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Loyiha to'xtatildi.")
