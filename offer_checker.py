import logging
import os
from datetime import datetime, timedelta
from database import Database
import aiohttp
import asyncio
import json

# Настройка логирования
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

current_date = datetime.now().strftime("%Y-%m-%d")
log_file = f"{log_dir}/offer_checker_{current_date}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Telegram bot token и chat_id
TOKEN = '8038814392:AAEj-Yh0SiujDSmtT7KWpFGErCn-crEF2ts'
CHAT_ID = -1002578623157

# Сообщения оффера (из tg_bot_async.py)
OFFER_MESSAGE = {
    'ru': """Хотите запустить свой бизнес с нуля — быстро, легально и без лишних хлопот?
Мы берём на себя весь процесс:
✔ Регистрация ИП,
✔ Открытие банковского счёта,
✔ Консультации по ключевым вопросам на старте.

Реальная рыночная стоимость пакета — ~ 3.000.000 сум.
Но для вас, по специальным условиям — всего 425.000 сум.

Что это даёт:
✅ Экономия времени и нервов,
✅ Грамотное оформление без ошибок,
✅ Поддержка экспертов на старте, чтобы вы сосредоточились на развитии бизнеса.

Если вы готовы начать уверенно — оставьте заявку, и мы запустим ваш бизнес под ключ.""",
    'uz': """💥 Biznesingizni tez va ortiqcha tashvishsiz yo'lga qo'yishni xohlaysizmi?
Biz siz uchun barcha ishlarni amalga oshiramiz:
✔ YaTTni ro'yxatdan o'tkazamiz,
✔ Bank hisobraqamini ochamiz,
✔ Boshlang'ich bosqichda maslahatlar bilan ko'maklashamiz.

💰 Odatdagi narxi — taxminan 3.000.000 so'm,
🔥 Siz uchun — bor-yo'g'i 425.000 so'm!

Nimalardan bahramand bo'lasiz:
✅ Vaqt va kuchingizni tejaysiz,
✅ Hujjatlar xatosiz rasmiylashtiriladi,
✅ Biznesingizga e'tibor qaratishingiz uchun mutaxassislar yordamidan foydalanasiz.

Boshlashga tayyor bo'lsangiz — quyidagi tugmani bosing!"""
}

OFFER_BUTTON = {
    'ru': "Оставить заявку",
    'uz': "Ariza qoldirish"
}

async def send_offer_to_user(chat_id: int, lang: str):
    """Отправка оффера пользователю в Telegram"""
    try:
        async with aiohttp.ClientSession() as session:
            markup = {
                "inline_keyboard": [[
                    {"text": OFFER_BUTTON[lang], "callback_data": "submit_contact"}
                ]]
            }
            params = {
                "chat_id": chat_id,
                "text": OFFER_MESSAGE[lang],
                "reply_markup": json.dumps(markup)
            }
            async with session.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                params=params
            ) as response:
                if response.status != 200:
                    logger.error(f"Ошибка отправки оффера для chat_id {chat_id}: {await response.text()}")
                    return False
                logger.info(f"Оффер успешно отправлен для chat_id {chat_id}")
                return True
    except Exception as e:
        logger.error(f"Ошибка при отправке оффера для chat_id {chat_id}: {str(e)}")
        return False

async def check_and_send_offers():
    """Проверка пользователей и отправка офферов"""
    try:
        logger.info("Начало проверки пользователей для отправки офферов")
        db = Database()
        users = db.get_all_users()

        if not users:
            logger.warning("Нет пользователей в базе данных")
            return

        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)

        for user_id, user_data in users.items():
            lang = user_data.get('lang', 'ru')  # По умолчанию 'ru', если язык не указан
            last_interaction = user_data.get('last_interaction')
            offer_scheduled_at = user_data.get('offer_scheduled_at')

            # Пропускаем, если оффер уже отправлен
            if offer_scheduled_at:
                logger.debug(f"Пропущен user_id {user_id}: оффер уже отправлен")
                continue

            # Пропускаем, если last_interaction отсутствует или менее 1 часа назад
            if not last_interaction or last_interaction > one_hour_ago:
                logger.debug(f"Пропущен user_id {user_id}: last_interaction отсутствует или слишком недавний")
                continue

            # Отправляем оффер
            success = await send_offer_to_user(user_id, lang)
            if success:
                # Обновляем offer_scheduled_at
                user_data['offer_scheduled_at'] = now
                db.save_user_state(user_id, user_data)
                db.log_action(user_id, 'offer_sent', {'lang': lang})

        logger.info("Проверка пользователей завершена")

    except Exception as e:
        logger.error(f"Ошибка при проверке пользователей: {str(e)}")

if __name__ == '__main__':
    asyncio.run(check_and_send_offers())