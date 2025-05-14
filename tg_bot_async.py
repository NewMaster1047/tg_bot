import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import logging
import os
from datetime import datetime
from database import Database
import aiohttp
from analyze_users import analyze_users_combined

# Настройка логирования
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

current_date = datetime.now().strftime("%Y-%m-%d")
log_file = f"{log_dir}/bot_{current_date}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Bot configuration
TOKEN = '8038814392:AAEj-Yh0SiujDSmtT7KWpFGErCn-crEF2ts'

# Инициализация базы данных
db = Database(
    host="localhost",
    user="root",
    password="",
    database="tg_bot"
)

# Language questions and PDFs
questions_data = {
    'ru': [
        {"q": "Как вы обычно решаете рабочие задачи?", "options": [("⚡️Действую сразу, разбираясь по ходу.", "A"), ("🔍Сначала собираю информацию.", "B"), ("🤝Передаю задачу другому.", "C")]},
        {"q": "Что вам больше нравится?", "options": [("🗣️ Общение", "A"), ("💻 Онлайн и цифры", "B"), ("✨ Красота и новое", "C")]},
        {"q": "Какая ваша главная сильная сторона?", "options": [("⚡️ Энергия", "A"), ("🔍 Внимание к деталям", "B"), ("🎨 Вкус и стиль", "C")]},
        {"q": "Что сильнее мотивирует вас на работе?", "options": [("🏆 Победа и признание", "A"), ("💛 Ощущение пользы и смысла", "B"), ("📋 Эффективность и порядок", "C")]},
        {"q": "Какой стиль жизни вам ближе?", "options": [("🏃 Активный", "A"), ("🧘 Спокойный", "B"), ("🌈 Разнообразный", "C")]},
        {"q": "Что вас больше всего вдохновляет?", "options": [("📈 Рост и успех", "A"), ("🤝 Помощь людям", "B"), ("🎨 Красота", "C")]},
        {"q": "Если бы вы создали свой бренд, что было бы на первом плане?", "options": [("✨ Яркий стиль", "A"), ("🛠️ Высокое качество продукта", "B"), ("🤝 Польза для людей и общества", "C")]},
        {"q": "Что для вас важнее в работе?", "options": [("❤️Любовь к делу", "A"), ("💰 Доход", "B"), ("🕊️ Свобода", "C")]},
        {"q": "Какой формат бизнеса вам интересен?", "options": [("🌐 Онлайн", "A"), ("🏬 Офлайн", "B"), ("🔀 Смешанный", "C")]},
        {"q": "Чем бы вы занимались даже бесплатно?", "options": [("📚 Обучением или помощью", "A"), ("🎨 Красотой или творчеством", "B"), ("💻 Онлайн-проектами или соцсетями", "C")]},
        {"q": "Представьте: вы на старте бизнеса. Какой ваш первый шаг?", "options": [("📣 Заявлю о себе в соцсетях", "A"), ("📊 Сделаю бизнес-план и просчитаю все", "B"), ("🤝 Соберу единомышленников и команду", "C")]},
    ],
    'uz': [
        {"q": "Ish vazifalarini qanday hal etasiz?", "options": [("Darhol boshlayman ⚡️", "A"), ("Ma'lumot yig'aman 📚", "B"), ("Boshqalarga topshiraman 🤝", "C")]},
        {"q": "Qaysi vazifa sizga ko'proq yoqadi?", "options": [("Muammolarni hal qilish 🛠️", "A"), ("Jarayonlarni yaxshilash 🔧", "B"), ("Yangi loyihalarni boshlash 🚀", "C")]},
        {"q": "Sizga nima ko'proq yoqadi?", "options": [("Muloqot 🗣️", "A"), ("Internet va raqamlar 💻", "B"), ("Go'zallik va yangiliklar ✨", "C")]},
        {"q": "Sizning eng asosiy kuchli tomoningiz qaysi?", "options": [("G'ayrat 💪", "A"), ("Tafsilotlarga e'tibor 🔍", "B"), ("Did va uslub 🎨", "C")]},
        {"q": "Ishda sizni nima rag'batlantiradi?", "options": [("G'alaba va e'tirof 🏆", "A"), ("Foydali ish ❤️", "B"), ("Samaradorlik va tartib 📊", "C")]},
        {"q": "Qanday hayot tarzi yoqadi?", "options": [("Faol 💥", "A"), ("Tinch 🌿", "B"), ("Rang-barang 🌈", "C")]},
        {"q": "Stressni qanday yengasiz?", "options": [("Sport yoki yurish 🏃‍♂️", "A"), ("Do'stlar bilan gaplashib", "B"), ("Yolg'izlikda dam olib 🌙", "C")]},
        {"q": "Sizni eng ko'p nima ruhlantiradi?", "options": [("O'sish va muvaffaqiyat 🚀", "A"), ("Insonlarga yordam ko'rsatish 🤝", "B"), ("Go'zallik 🎨", "C")]},
        {"q": "Muvaffaqiyat siz uchun nima?", "options": [("Pul va obro' 💰✨", "A"), ("Ma'no va qadriyat 💡❤️", "B"), ("Erkinlik va vaqt 🕊️⏰", "C")]},
        {"q": "Yangi narsalarni qanday o'rganasiz?", "options": [("Amalda sinab ko'rib 🔧💥", "A"), ("Kitob yoki kurslardan 📚🎓", "B"), ("Boshqalardan o'rganib 👥💬", "C")]},
        {"q": "Sizni orzuyingizdagi natijaga eng tez yetkazadigan narsa nima, deb o'ylaysiz?", "options": [("Yaxshi jamoa 👥", "A"), ("To'g'ri strategiya 📊", "B"), ("Moliyaviy resurslar 💰", "C")]},
    ]
}

data = {
    'questions': questions_data,
    'pdf_links': {
        "ru": {
            'A': ['pdfs/Бизнес-план Ивент агентства от Azma Finance.pdf', 'pdfs/Бизнес-план по продаже трендовых товаров  от Azma Finance.pdf', 'pdfs/Бизнес-план IT Стартапа от Azma Finance.pdf', 'pdfs/Бизнес-план онлайн школы  от Azma Finance .pdf'],
            'B': ['pdfs/Бизнес-план центра детского развития  от Azma Finance.pdf', 'pdfs/Бизнес-план  онлайн школы по саморазвитию  от Azma Finance.pdf', 'pdfs/Бизнес-план салона красоты от Azma Finance.pdf', 'pdfs/Бизнес-план свадебного агентства от Azma Finance.pdf'],
            'C': ['pdfs/Бизнес-план Консалтинговой компании  от Azma Finance .pdf', 'pdfs/Бизнес-план центра репетиторства  от Azma Finance.pdf', 'pdfs/Бизнес-план  B2B услуг в сфере HR и финансов от Azma Finance.pdf', 'pdfs/Бизнес-план Рекламного агентства от Azma Finance .pdf'],
        },
        "uz": {
            'A': ['pdfs/Azma Finance’dan  event agentlik    biznes-rejasi  .pdf', 'pdfs/Azma Finance’dan  trenddagi tovarlarni sotish bo‘yicha biznes-reja  .pdf', 'pdfs/Azma Finance’dan  IT startapining biznes-rejasi.pdf', 'pdfs/Azma Finance’dan onlayn maktab biznes rejasi .pdf'],
            'B': ['pdfs/Azma Finance’dan  bolalar rivojlanish markazi   biznes-rejasi  .pdf', 'pdfs/Azma Finance’dan  onlayn maktabning biznes-rejasi  .pdf', "pdfs/Azma Finance’dan g'ozallik salonining biznes-rejasi  .pdf", "pdfs/Azma Finance’dan t'oy agentligining   biznes-rejasi  .pdf"],
            'C': ["pdfs/Azma Finance'dan Konsalting kompaniyasining biznes rejasi.pdf", "pdfs/Azma Finance’dan repetitorlik markazining biznes rejasi.pdf", 'pdfs/Azma Finance’dan HR va moliya sohasidagi B2B xizmatlarining biznes-rejasi.pdf', 'pdfs/Azma Finance’dan reklama agentligini biznes rejasi.pdf'],
        }
    },
    "type_img": {
        "A": "img/1.jpg",
        "B": "img/2.jpg",
        "C": "img/3.jpg"
    },
    'results': {
        'ru': {
            'A': 'Тип 1 (Инноватор): \n⚡️ Ивент-агентство \n⚡️ Продажа трендовых товаров \n⚡️ Startup в IT или e-commerce \n⚡️ Онлайн школа',
            'B': 'Тип 2 (Сердце): \n💛 Центр детского развития \n💛 Онлайн-курсы по саморазвитию \n💛 Салон красоты \n💛 Свадебное агентство',
            'C': 'Тип 3 (Стратег): \n🧩 Консалтинг \n🧩 Центр репетиторства \n🧩 B2B-услуги (HR, финансы) \n🧩 Рекламное Агентство'
        },
        'uz': {
            'A': '1-tur (Innovator): \n⚡️ Tadbirlar agentligi \n⚡️ Zamonaviy mahsulotlar savdosi \n⚡️ IT yoki elektron tijorat sohasidagi startap \n⚡️ Onlayn maktab',
            'B': "2-tur (Yurak): \n💛 Bolalar rivojlanish markazi \n💛 O'zini rivojlantirish bo'yicha onlayn kurslar \n💛 Go'zallik saloni \n💛 To'y agentligi",
            'C': '3-tur (Strateg): \n🧩 Konsalting \n🧩 Repetitorlik markazi \n🧩 B2B xizmatlari (masalan, HR yoki moliya sohasida) \n🧩 Reklama agentligi'
        }
    },
    'start_text': {
        'ru': "✨Сейчас я задам вам несколько вопросов — отвечайте честно, и в конце вы получите советы, какой бизнес лучше всего вам подойдёт!✨\n\nИспользуйте /restart, чтобы начать заново.",
        'uz': "✨Hozir sizga bir nechta savol beraman — to'g'ri javob bering va oxirida o'zingizga eng mos keladigan biznes haqida maslahatlar olasiz!✨\n\nQayta boshlash uchun /restart dan foydalaning."
    },
    'request_contact': {
        'ru': "Пожалуйста, нажмите кнопку ниже, чтобы отправить ваш номер телефона 📞",
        'uz': "Iltimos, telefon raqamingizni yuborish uchun quyidagi tugmani bosing 📞"
    },
    'offer_message': {
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
    },
    'offer_button': {
        'ru': "Оставить заявку",
        'uz': "Ariza qoldirish"
    },
    'offer_url': "https://azma.uz/ru/my/get-started/open-ip",
    "dpf_message": {
        "ru": "📄 Вот вам бизнес-план:",
        "uz": "📄 Mana siz uchun biznes-plan:"
    }
}

async def schedule_offer_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, lang: str, delay: int = 10):
    try:
        await asyncio.sleep(delay)
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton(text=data['offer_button'][lang], callback_data="submit_contact")
        ]])
        await context.bot.send_message(chat_id=chat_id, text=data['offer_message'][lang], reply_markup=markup)
        # Сохраняем время планирования оффера
        user_state = db.get_user_state(chat_id)
        user_state['offer_scheduled_at'] = datetime.now()
        db.save_user_state(chat_id, user_state)
    except Exception as e:
        logger.error(f"Ошибка при отправке отложенного предложения для chat_id {chat_id}: {str(e)}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        user_state = db.get_user_state(user_id)
        db.save_user_state(user_id, user_state)

        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("🇺🇿UZ", callback_data="lang_uz"),
            InlineKeyboardButton("🇷🇺RU", callback_data="lang_ru")
        ]])
        await update.message.reply_text("Tilni tanlang \nВыберите язык", reply_markup=markup)
    except Exception as e:
        logger.error(f"Ошибка в start для user_id {user_id}: {str(e)}")

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        user_state = db.get_user_state(user_id)
        user_state.update({
            'lang': None,
            'step': 0,
            'scores': {'A': 0, 'B': 0, 'C': 0},
            'waiting_for_contact': False,
            'contact_info': None,
            'offer_scheduled_at': None
        })
        db.save_user_state(user_id, user_state)

        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("🇺🇿UZ", callback_data="lang_uz"),
            InlineKeyboardButton("🇷🇺RU", callback_data="lang_ru")
        ]])
        await update.message.reply_text("Tilni tanlang \nВыберите язык", reply_markup=markup)
    except Exception as e:
        logger.error(f"Ошибка в restart для user_id {user_id}: {str(e)}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка комбинированного отчета (за сегодня и за все время) в Telegram-группу"""
    try:
        user_id = update.effective_user.id
        logger.info(f"Команда /stats вызвана пользователем {user_id}")
        
        # Ограничиваем доступ
        allowed_users = [7969873927]  # Замените на список разрешенных user_id
        if user_id not in allowed_users:
            await update.message.reply_text("У вас нет доступа к этой команде.")
            return

        # Вызываем комбинированный анализ
        report = await analyze_users_combined(send_to_telegram=True)
        
        # Отправляем подтверждение пользователю
        await update.message.reply_text("Отчет отправлен в группу!")
    except Exception as e:
        logger.error(f"Ошибка в stats для user_id {user_id}: {str(e)}")
        await update.message.reply_text("Произошла ошибка при отправке отчета.")

async def select_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        lang = query.data.split("_")[1]
        user_id = query.from_user.id

        user_state = db.get_user_state(user_id)
        user_state.update({
            'lang': lang,
            'step': 0,
            'scores': {'A': 0, 'B': 0, 'C': 0},
            'waiting_for_contact': False,
            'contact_info': user_state.get('contact_info'),  # Сохраняем существующий контакт
            'offer_scheduled_at': None
        })
        db.save_user_state(user_id, user_state)

        await query.message.delete()
        await context.bot.send_message(query.message.chat_id, data['start_text'][lang])
        await send_question(context, query.message.chat_id, user_id)
    except Exception as e:
        logger.error(f"Ошибка в select_language для user_id {user_id}: {str(e)}")

async def send_question(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int):
    try:
        user_state = db.get_user_state(user_id)
        lang = user_state['lang']
        step = user_state['step']
        questions = data['questions'][lang]

        if step < len(questions):
            q = questions[step]
            buttons = [[InlineKeyboardButton(text, callback_data=f"ans_{tag}")] for text, tag in q['options']]
            if step > 0:
                buttons.append([InlineKeyboardButton(
                    "⬅ Назад" if lang == 'ru' else "⬅ Orqaga",
                    callback_data="go_back"
                )])
            markup = InlineKeyboardMarkup(buttons)
            progress = f"Вопрос {step + 1}/{len(questions)}"
            await context.bot.send_message(chat_id, f"{progress}\n{q['q']}", reply_markup=markup)
        else:
            await request_contact_info(context, chat_id, user_id)
    except Exception as e:
        logger.error(f"Ошибка в send_question для user_id {user_id}: {str(e)}")

async def request_contact_info(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int):
    try:
        user_state = db.get_user_state(user_id)
        lang = user_state['lang']
        
        user_state['waiting_for_contact'] = True
        db.save_user_state(user_id, user_state)

        markup = ReplyKeyboardMarkup([[KeyboardButton(
            "📞 Отправить контакт" if lang == 'ru' else "📞 Kontaktni yuborish",
            request_contact=True
        )]], one_time_keyboard=True, resize_keyboard=True)
        await context.bot.send_message(chat_id, data['request_contact'][lang], reply_markup=markup)
    except Exception as e:
        logger.error(f"Ошибка в request_contact_info для user_id {user_id}: {str(e)}")

async def handle_contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        contact = update.message.contact
        
        user_state = db.get_user_state(user_id)
        lang = user_state['lang'] or 'ru'
        
        if contact:
            contact_info = {
                'phone_number': contact.phone_number,
                'first_name': contact.first_name,
                'last_name': contact.last_name if contact.last_name else None
            }
            
            # Обновляем состояние с новой контактной информацией
            user_state.update({
                'contact_info': contact_info,
                'waiting_for_contact': False
            })
            success = db.save_user_state(user_id, user_state)
            
            if not success:
                logger.error(f"Не удалось сохранить контактную информацию для user_id {user_id}")
                await update.message.reply_text(
                    "Произошла ошибка при сохранении контакта. Попробуйте еще раз." if lang == 'ru' else
                    "Kontaktni saqlashda xatolik yuz berdi. Yana urinib ko‘ring.",
                    reply_markup=ReplyKeyboardRemove()
                )
                return
            
            # Логируем действие
            db.log_action(user_id, 'contact_provided', {'phone_number': contact.phone_number})
            
            # Удаляем клавиатуру
            await update.message.reply_text(
                "Спасибо! Ваш контакт получен." if lang == 'ru' else "Rahmat! Kontaktingiz qabul qilindi.",
                reply_markup=ReplyKeyboardRemove()
            )
            
            await send_result(context, update.effective_chat.id, user_id)
    except Exception as e:
        logger.error(f"Ошибка в handle_contact_info для user_id {user_id}: {str(e)}")
        await update.message.reply_text(
            "Произошла ошибка. Попробуйте еще раз." if user_state.get('lang') == 'ru' else
            "Xatolik yuz berdi. Yana urinib ko‘ring.",
            reply_markup=ReplyKeyboardRemove()
        )

async def send_result(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int):
    try:
        user_state = db.get_user_state(user_id)
        scores = user_state['scores']
        lang = user_state['lang']
        result_type = max(scores, key=scores.get)
        result_text = data['results'][lang][result_type]
        pdf_links = data['pdf_links'][lang][result_type]
        dpf_message = data['dpf_message'][lang]
        photo_path = data["type_img"][result_type]
        result_text = f"Ваш результат — {result_text}" if lang == 'ru' else f"Sizning natijangiz — {result_text}"

        if not os.path.exists(photo_path):
            logger.warning(f"Изображение {photo_path} не найдено, пропускаем отправку фото")
        else:
            with open(photo_path, 'rb') as photo:
                await context.bot.send_photo(chat_id, photo, caption=result_text)

        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "Хочу!" if lang == 'ru' else "Hohlayman!",
                callback_data=f"show_all_{lang}"
            )
        ]])
        await context.bot.send_message(chat_id, dpf_message)
        
        for pdf in pdf_links:
            if not os.path.exists(pdf):
                logger.warning(f"PDF {pdf} не найден, пропускаем")
            else:
                with open(pdf, 'rb') as file:
                    await context.bot.send_document(chat_id, file)

        await context.bot.send_message(
            chat_id,
            "Хотите посмотреть все варианты?" if lang == 'ru' else "Barcha variantlarni ko'rishni hohlaysizmi?",
            reply_markup=markup
        )

        asyncio.create_task(schedule_offer_message(context, chat_id, lang))
    except Exception as e:
        logger.error(f"Ошибка в send_result для user_id {user_id}: {str(e)}")

async def show_all_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        lang = query.data.split("_")[2]
        chat_id = query.message.chat_id
        user_id = query.from_user.id

        all_results = data['results'][lang]
        for result_type, result_text in all_results.items():
            pdf_links = data["pdf_links"][lang][result_type]
            await context.bot.send_message(chat_id, f"{result_text}")
            await context.bot.send_message(chat_id, f"{data['dpf_message'][lang]}")
            for pdf in pdf_links:
                if not os.path.exists(pdf):
                    logger.warning(f"PDF {pdf} не найден, пропускаем")
                else:
                    with open(pdf, 'rb') as file:
                        await context.bot.send_document(chat_id, file)

        await query.answer()
    except Exception as e:
        logger.error(f"Ошибка в show_all_options для user_id {user_id}: {str(e)}")

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        user_id = query.from_user.id
        chat_id = query.message.chat_id
        callback_data = query.data

        user_state = db.get_user_state(user_id)

        if callback_data.startswith("ans_"):
            answer = callback_data.split("_")[1]
            user_state['scores'][answer] = user_state['scores'].get(answer, 0) + 1
            user_state['step'] += 1
            db.save_user_state(user_id, user_state)
            await query.answer()
            await query.message.delete()
            await send_question(context, chat_id, user_id)

        elif callback_data == "go_back":
            if user_state['step'] > 0:
                user_state['step'] -= 1
                db.save_user_state(user_id, user_state)
            await query.answer()
            await query.message.delete()
            await send_question(context, chat_id, user_id)

    except Exception as e:
        logger.error(f"Ошибка в handle_answer для user_id {user_id}: {str(e)}")

async def handle_submit_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        user_id = query.from_user.id
        chat_id = query.message.chat_id
        username = query.from_user.username or "No username"
        
        user_state = db.get_user_state(user_id)
        lang = user_state['lang'] or 'ru'
        contact_info = user_state.get('contact_info')

        if not contact_info:
            # Если контакт не предоставлен, просим отправить
            await query.answer("Сначала предоставьте контактную информацию!")
            await request_contact_info(context, chat_id, user_id)
            return

        # Формируем сообщение для отправки
        contact_str = f"Номер: {contact_info['phone_number']}"
        if contact_info.get('first_name'):
            contact_str += f"\nИмя: {contact_info['first_name']}"
        if contact_info.get('last_name'):
            contact_str += f"\nФамилия: {contact_info['last_name']}"

        async with aiohttp.ClientSession() as session:
            params = {
                "chat_id": -1002578623157,
                "text": f"✅ Новая заявка!\n👤 Пользователь: @{username}\n📞 Контакт:\n{contact_str}"
            }
            async with session.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                params=params
            ) as response:
                if response.status != 200:
                    logger.error(f"Ошибка API Telegram: {await response.text()}")
                    await query.answer("Ошибка при отправке заявки!")
                    return

        # Логируем действие
        db.log_action(user_id, 'application_submitted', {'contact_info': contact_info})

        await query.answer("✅ Ваша заявка отправлена!")
        await context.bot.send_message(
            chat_id,
            "Спасибо! Мы свяжемся с вами в ближайшее время." if lang == 'ru'
            else "Rahmat! Tez orada siz bilan bog'lanamiz."
        )

    except Exception as e:
        logger.error(f"Ошибка в handle_submit_contact для user_id {user_id}: {str(e)}")
        await query.answer("Ошибка при отправке заявки!")
        await context.bot.send_message(
            chat_id,
            "Произошла ошибка. Попробуйте еще раз." if user_state.get('lang') == 'ru'
            else "Xatolik yuz berdi. Yana urinib ko‘ring."
        )

async def restore_pending_offers(application):
    now = datetime.now()
    for user_id, user in db.get_all_users().items():
        scheduled_at = user.get("offer_scheduled_at")
        if scheduled_at:
            delta = (now - scheduled_at).total_seconds()
            if delta < 3600:
                delay = 3600 - delta
                logger.info(f"Восстановление таймера для user_id {user_id}, осталось {delay} сек")
                asyncio.create_task(schedule_offer_message(application.bot, user_id, user['lang'], delay))

def main():
    try:
        # Очистка устаревших записей при запуске
        db.cleanup_old_records(days=7)
        
        application = Application.builder().token(TOKEN).build()

        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("restart", restart))
        application.add_handler(CommandHandler("stats", stats))
        application.add_handler(CallbackQueryHandler(select_language, pattern="^lang_"))
        application.add_handler(CallbackQueryHandler(handle_answer, pattern="^ans_"))
        application.add_handler(CallbackQueryHandler(handle_answer, pattern="^go_back$"))
        application.add_handler(CallbackQueryHandler(show_all_options, pattern="show_all_"))
        application.add_handler(CallbackQueryHandler(handle_submit_contact, pattern="^submit_contact$"))
        application.add_handler(MessageHandler(filters.CONTACT, handle_contact_info))

        # Запускаем восстановление ожидающих офферов в том же event loop
        application.post_init = restore_pending_offers

        logger.info("Запуск бота...")
        application.run_polling()

    except Exception as e:
        logger.error(f"Ошибка в main: {str(e)}")
        raise

if __name__ == '__main__':
    main()