import telebot
from telebot import types
from collections import defaultdict
import threading
import time

bot = telebot.TeleBot('8038814392:AAEj-Yh0SiujDSmtT7KWpFGErCn-crEF2ts')  # <- Replace with your actual bot token

# Language questions and PDFs
questions_data = {
    'ru': [
        {"q": "Как вы обычно решаете рабочие задачи?", "options": [("Действую сразу, разбираясь по ходу.", "A"), ("Сначала собираю информацию.", "B"), ("Передаю задачу другому.", "C")]},
        {"q": "Что вам больше нравится?", "options": [("Общение", "A"), ("Онлайн и цифры", "B"), ("Красота и новое", "C")]},
        {"q": "Какая ваша главная сильная сторона?", "options": [("Энергия", "A"), ("Внимание к деталям", "B"), ("Вкус и стиль", "C")]},
        {"q": "Что сильнее мотивирует вас на работе?", "options": [("Победа и признание", "A"), ("Ощущение пользы и смысла", "B"), ("Эффективность и порядок", "C")]},
        {"q": "Какой стиль жизни вам ближе?", "options": [("Активный", "A"), ("Спокойный", "B"), ("Разнообразный", "C")]},
        {"q": "Что вас больше всего вдохновляет?", "options": [("Рост и успех", "A"), ("Помощь людям", "B"), ("Красота", "C")]},
        {"q": "Если бы вы создали свой бренд, что было бы на первом плане?", "options": [("Яркий стиль", "A"), ("Высокое качество продукта", "B"), ("Польза для людей и общества", "C")]},
        {"q": "Что для вас важнее в работе?", "options": [("Свобода", "A"), ("Доход", "B"), ("Любовь к делу", "C")]},
        {"q": "Какой формат бизнеса вам интересен?", "options": [("Онлайн", "A"), ("Офлайн", "B"), ("Смешанный", "C")]},
        {"q": "Чем бы вы занимались даже бесплатно?", "options": [("Обучением или помощью", "A"), ("Красотой или творчеством", "B"), ("Онлайн-проектами или соцсетями", "C")]},
        {"q": "Представьте: вы на старте бизнеса. Какой ваш первый шаг?", "options": [("Заявлю о себе в соцсетях", "A"), ("Сделаю бизнес-план и просчитаю цифры", "B"), ("Соберу единомышленников и команду", "C")]},
    ],
    'uz': [
        {"q": "Ish vazifalarini qanday hal etasiz?", "options": [("Darhol boshlayman", "A"), ("Ma’lumot yig‘amanм", "B"), ("Boshqalarga topshiraman.", "C")]},
        {"q": "Qaysi vazifa sizga ko‘proq yoqadi?", "options": [("Muammolarni hal qilish", "A"), ("Jarayonlarni yaxshilash", "B"), ("Yangi loyihalarni boshlash", "C")]},
        {"q": "Sizga nima ko‘proq yoqadi?", "options": [("Muloqot", "A"), ("Internet va raqamlar", "B"), ("Go‘zallik va yangiliklarmi", "C")]},
        {"q": "Sizning eng asosiy kuchli tomoningiz qaysi?", "options": [("G'ayrat", "A"), ("Tafsilotlarga e’tibor", "B"), ("Did va uslub", "C")]},
        {"q": "Ishda sizni nima rag‘batlantiradi?", "options": [("G‘alaba va e’tirof", "A"), ("Foydali ish", "B"), ("Samaradorlik va tartib", "C")]},
        {"q": "Qanday hayot tarzi yoqadi?", "options": [("Faol", "A"), ("Tinch", "B"), ("Rang-barang", "C")]},
        {"q": "Stressni qanday yengasiz?", "options": [("Sport yoki yurish", "A"), ("Do‘stlar bilan gaplashib", "B"), ("Yolg‘izlikda dam olib", "C")]},
        {"q": "Sizni eng ko‘p nima ruhlantiradi?", "options": [("O‘sish va muvaffaqiyat", "A"), ("Insonlarga yordam ko‘rsatish", "B"), ("Go‘zallik", "C")]},
        {"q": "Muvaffaqiyat siz uchun nima?", "options": [("Pul va obro‘", "A"), ("Ma’no va qadriyat", "B"), ("Erkinlik va vaqt", "C")]},
        {"q": "Yangi narsalarni qanday o‘rganasiz?", "options": [("Amalda sinab ko‘rib", "A"), ("Kitob yoki kurslardan", "B"), ("Boshqalardan o‘rganib", "C")]},
        {"q": "Sizni orzuyingizdagi natijaga eng tez yetkazadigan narsa nima, deb o‘ylaysiz?", "options": [("Yaxshi jamoa", "A"), ("To‘g‘ri strategiya", "B"), ("Moliyaviy resurslar", "C")]},
    ]
}

data = {
    'questions': questions_data,
    'pdf_links': {
        "ru": {
            'A': 'https://azma.uz/tpost/d5tgd89h51-biznes-plan-po-otkritiyu-ivent-agentstva',
            'B': 'https://azma.uz/tpost/s1vva54bu1-polnii-biznes-plan-tsentra-detskogo-razv',
            'C': 'https://azma.uz/tpost/7hvjkjo6e1-biznes-plan-tsentra-repetitorstva-v-uzbe',
        },
        "uz": {
            'A': 'https://azma.uz/tpost/yompspm931-ozbekiston-uchun-iventagentlik-ochish-bo',
            'B': 'https://azma.uz/tpost/ebisnrnzn1-ozbekistonda-bolalar-rivojlanish-markazi',
            'C': 'https://azma.uz/tpost/5aibx5dfj1-repetitorlik-markazi-ozbekistonda-2025-i',
        }
    },
    "type_img": {
        "A": "img/1.jpg",
        "B": "img/2.jpg",
        "C": "img/3.jpg"
    },
    'results': {
        'ru': {
            'A': 'Ваш результат — Тип 1 (Драйвер): \n⚡️ Ивент-агентство \n⚡️ Личный бренд и блоги \n⚡️ Продажа трендовых товаров \n⚡️ Startup в IT или e-commerce',
            'B': 'Ваш результат — Тип 2 (Сердце): \n💛 Центр детского развития \n💛 Онлайн-курсы по саморазвитию \n💛 Социальное кафе \n💛 Магазин hand-made товаров \n💛 Сервис поддержки мам и детей',
            'C': 'Ваш результат — Тип 3 (Стратег): \n🧩 Консалтинг или бухгалтерия \n🧩 Онлайн-школа по  маркетингу \n🧩 Центр репетиторства \n🧩 B2B-услуги (HR, финансы) \n🧩 Создание цифровых продуктов (шаблоны, гайды)'
        },
        'uz': {
            'A': 'Sizning natijangiz — 1-tur (Haydovchi): \n⚡️ Tadbirlar agentligi \n⚡️ Shaxsiy brend va bloglar \n⚡️ Zamonaviy mahsulotlar savdosi \n⚡️ IT yoki elektron tijorat sohasidagi startap \n⚡️ Yetkazib berish franshizasi',
            'B': 'Sizning natijangiz — 2-tur (Yurak): \n💛 Bolalar rivojlanish markazi \n💛 O‘zini rivojlantirish bo‘yicha onlayn kurslar \n💛 Ijtimoiy qahvaxona \n💛 Qo‘lda yasalgan buyumlar do‘koni \n💛 Onalar va bolalarni qo‘llab-quvvatlash xizmati',
            'C': 'Sizning natijangiz — 3-tur (Strateg): \n🧩 Maslahat yoki buxgalteriya xizmatlari \n🧩 Excel yoki marketing bo‘yicha onlayn maktab \n🧩 Jarayonlarni avtomatlashtirish agentligi \n🧩 B2B xizmatlari (masalan, HR yoki moliya sohasida) \n🧩 Raqamli mahsulotlar yaratish (andozalar, qo‘llanmalar)'
        }
    },
    'start_text': {
        'ru': "Сейчас я задам вам несколько вопросов — отвечайте честно, и в конце вы получите советы, какой бизнес лучше всего вам подойдёт!",
        'uz': "Hozir sizga bir nechta savol beraman — to‘g‘ri javob bering va oxirida o‘zingizga eng mos keladigan biznes haqida maslahatlar olasiz!"
    },
    'request_contact': {
        'ru': "Пожалуйста, введите ваше ФИО и номер телефона в формате:\n\nИванов Иван Иванович +998901234567",
        'uz': "Iltimos, ism-familyangiz va telefon raqamingizni quyidagi formatda kiriting:\n\nIvanov Ivan Ivanovich +998901234567"
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

        'uz': """💥 Biznesingizni tez va ortiqcha tashvishsiz yo‘lga qo‘yishni xohlaysizmi?
Biz siz uchun barcha ishlarni amalga oshiramiz:
✔ YaTTni ro‘yxatdan o‘tkazamiz,
✔ Bank hisobraqamini ochamiz,
✔ Boshlang‘ich bosqichda maslahatlar bilan ko‘maklashamiz.

💰 Odatdagi narxi — taxminan 3.000.000 so‘m,
🔥 Siz uchun — bor-yo‘g‘i 425.000 so‘m!

Nimalardan bahramand bo‘lasiz:
✅ Vaqt va kuchingizni tejaysiz,
✅ Hujjatlar xatosiz rasmiylashtiriladi,
✅ Biznesingizga e‘tibor qaratishingiz uchun mutaxassislar yordamidan foydalanasiz.

Boshlashga tayyor bo‘lsangiz — quyidagi tugmani bosing!"""
    },
    'offer_button': {
        'ru': "Оставить заявку",
        'uz': "Ariza qoldirish"
    },
    'offer_url': "https://azma.uz/ru/my/get-started/open-ip",
    "dpf_message": {
        "ru": "📄 Вот вам бизнес-план:",
        "uz": "📄 Mana siz uchun biznes-plan:",
    },
}

# User states
user_state = defaultdict(lambda: {
    'lang': None,
    'step': 0,
    'scores': {'A': 0, 'B': 0, 'C': 0},
    'waiting_for_contact': False,
    'contact_info': None
})

# Для хранения языковых предпочтений пользователей отдельно
user_languages = {}

def schedule_offer_message(chat_id, lang, delay=10):  # 3600 seconds = 1 hour
    def send_offer():
        time.sleep(delay)
        try:
            # Проверяем, что язык сохранен
            if lang is None:
                print(f"Language is None for chat_id: {chat_id}")
                return
                
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                text=data['offer_button'][lang],
                url=data['offer_url']
            ))
            bot.send_message(chat_id, data['offer_message'][lang], reply_markup=markup)
        except Exception as e:
            print(f"Failed to send offer message to {chat_id}: {e}")
    
    thread = threading.Thread(target=send_offer)
    thread.start()

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("UZ", callback_data="lang_uz"))
    markup.add(types.InlineKeyboardButton("RU", callback_data="lang_ru"))
    bot.send_message(message.chat.id, "Tilni tanlang \nВыберите язык", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def select_language(call):
    lang = call.data.split("_")[1]
    user_id = call.from_user.id

    user_state[user_id]['lang'] = lang
    user_languages[user_id] = lang  # Сохраняем язык отдельно
    
    user_state[call.from_user.id]['step'] = 0
    user_state[call.from_user.id]['scores'] = {'A': 0, 'B': 0, 'C': 0}
    user_state[call.from_user.id]['waiting_for_contact'] = False

    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, data['start_text'][lang])
    send_question(call.message.chat.id, call.from_user.id)

def send_question(chat_id, user_id):
    lang = user_state[user_id]['lang']
    step = user_state[user_id]['step']
    questions = data['questions'][lang]

    if step < len(questions):
        q = questions[step]
        markup = types.InlineKeyboardMarkup(row_width=1)
        for text, tag in q['options']:
            markup.add(types.InlineKeyboardButton(text, callback_data=f"ans_{tag}"))
        bot.send_message(chat_id, q['q'], reply_markup=markup)
    else:
        request_contact_info(chat_id, user_id)

def request_contact_info(chat_id, user_id):
    lang = user_state[user_id]['lang']
    user_state[user_id]['waiting_for_contact'] = True
    bot.send_message(chat_id, data['request_contact'][lang])

@bot.message_handler(func=lambda message: user_state.get(message.from_user.id, {}).get('waiting_for_contact', False))
def handle_contact_info(message):
    user_id = message.from_user.id
    contact_info = message.text
    
    user_state[user_id]['contact_info'] = contact_info
    user_state[user_id]['waiting_for_contact'] = False
    
    # Here you can save the contact info to database or file
    # For example:
    with open('contacts.txt', 'a', encoding='utf-8') as f:
        f.write(f"User ID: {user_id}, Contact: {contact_info}\n")
    
    send_result(message.chat.id, user_id)
    
    # Schedule offer message after 1 hour
    lang = user_state[user_id]['lang']
    schedule_offer_message(message.chat.id, lang)

def send_result(chat_id, user_id):
    scores = user_state[user_id]['scores']
    lang = user_state[user_id]['lang']
    result_type = max(scores, key=scores.get)
    result_text = data['results'][lang][result_type]
    pdf_link = data['pdf_links'][lang][result_type]
    dpf_message = data['dpf_message'][lang]
    photo_path = data["type_img"][result_type]

    with open(photo_path, 'rb') as photo:
        bot.send_photo(chat_id, photo, caption=result_text)


    markup = types.InlineKeyboardMarkup()
    if lang == 'ru':
        markup.add(types.InlineKeyboardButton(
            "Посмотреть все варианты", 
            callback_data=f"show_all_{lang}"
        ))
    else:
        markup.add(types.InlineKeyboardButton(
            "Barcha variantlarni ko'rish", 
            callback_data=f"show_all_{lang}"
        ))
    
    bot.send_message(chat_id, f"{dpf_message} \n\n{pdf_link}", reply_markup=markup)

    user_state.pop(user_id, None)

    # Schedule offer message after 1 hour
    if user_id in user_languages:
        schedule_offer_message(chat_id, user_languages[user_id])
    else:
        print(f"Language not found for user {user_id}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("show_all_"))
def show_all_options(call):
    lang = call.data.split("_")[2]
    user_id = call.from_user.id
    
    # Получаем все варианты результатов
    all_results = data['results'][lang]
    all_links = data['pdf_links']
    
    # Определяем основной тип результата пользователя
    if user_id in user_state:
        main_result = max(user_state[user_id]['scores'], key=user_state[user_id]['scores'].get)
    else:
        main_result = None
    
    # Отправляем все варианты кроме основного
    for result_type, result_text in all_results.items():
        print(result_type)
        print(data["type_img"][result_type])
        if result_type != main_result:
            photo_path = data["type_img"][result_type]
            with open(photo_path, 'rb') as photo:
                bot.send_photo(call.message.chat.id, photo, caption=result_text)
            bot.send_message(call.message.chat.id, 
                           f"{data['dpf_message'][lang]} \n\n{data['pdf_links'][lang][result_type]}")
    
    bot.answer_callback_query(call.id)



@bot.callback_query_handler(func=lambda call: call.data.startswith("ans_"))
def handle_answer(call):
    user_id = call.from_user.id
    answer = call.data.split("_")[1]
    user_state[user_id]['scores'][answer] += 1
    user_state[user_id]['step'] += 1

    bot.delete_message(call.message.chat.id, call.message.message_id)
    send_question(call.message.chat.id, user_id)

bot.polling(non_stop=True)
