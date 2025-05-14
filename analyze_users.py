import json
from datetime import datetime, date
import logging
import os
from database import Database
import aiohttp

# Настройка логирования
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

current_date = datetime.now().strftime("%Y-%m-%d")
log_file = f"{log_dir}/analyze_users_{current_date}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Telegram bot token
TOKEN = '8038814392:AAEj-Yh0SiujDSmtT7KWpFGErCn-crEF2ts'
CHAT_ID = -1002578623157

async def send_report_to_telegram(report: str):
    """Отправка отчета в Telegram-группу"""
    try:
        async with aiohttp.ClientSession() as session:
            params = {
                "chat_id": CHAT_ID,
                "text": report
            }
            async with session.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                params=params
            ) as response:
                if response.status != 200:
                    logger.error(f"Ошибка отправки отчета в Telegram: {await response.text()}")
                    return False
                logger.info("Отчет успешно отправлен в Telegram")
                return True
    except Exception as e:
        logger.error(f"Ошибка при отправке отчета в Telegram: {str(e)}")
        return False

def generate_report(users, title: str, current_date: str) -> str:
    """Генерация отчета на основе переданных данных пользователей"""
    if not users:
        return f"{title}\nНет данных для анализа\n{'=' * 50}\n"

    # Инициализация статистических данных
    total_users = len(users)
    lang_counts = {'ru': 0, 'uz': 0, 'unknown': 0}
    completed_test = 0
    result_types = {'A': 0, 'B': 0, 'C': 0}
    contacts_provided = 0
    max_questions = {'ru': 11, 'uz': 11}  # Количество вопросов для каждого языка

    # Анализ данных
    for user_id, user_data in users.items():
        # Подсчет по языкам
        lang = user_data['lang']
        if lang in lang_counts:
            lang_counts[lang] += 1
        else:
            lang_counts['unknown'] += 1

        # Проверка завершения теста
        lang = user_data['lang'] or 'ru'  # По умолчанию ru, если lang не указан
        if user_data['step'] >= max_questions.get(lang, 11):
            completed_test += 1

        # Определение типа результата (A, B, C)
        scores = user_data['scores']
        if scores and any(score > 0 for score in scores.values()):
            result_type = max(scores, key=scores.get)
            result_types[result_type] += 1

        # Проверка предоставления контактов
        if user_data['contact_info']:
            contacts_provided += 1

    # Формирование отчета
    report = f"{title} ({current_date})\n"
    report += "=" * 50 + "\n"
    report += f"Всего пользователей: {total_users}\n"
    report += "\nРаспределение по языкам:\n"
    for lang, count in lang_counts.items():
        report += f"  {lang}: {count} ({count/total_users*100:.1f}%)\n"
    report += f"\nЗавершили тест: {completed_test} ({completed_test/total_users*100:.1f}%)\n"
    report += "\nРаспределение результатов теста:\n"
    for r_type, count in result_types.items():
        report += f"  Тип {r_type}: {count} ({count/total_users*100:.1f}%)\n"
    report += f"\nПредоставили контакты: {contacts_provided} ({contacts_provided/total_users*100:.1f}%)\n"
    report += "=" * 50 + "\n"

    return report

async def analyze_users_today(send_to_telegram: bool = False) -> str:
    """Анализ данных пользователей за текущий день"""
    try:
        logger.info("Начало анализа данных пользователей за сегодня")
        db = Database()
        today = date.today()
        users = db.get_all_users()
        
        # Фильтрация пользователей по last_interaction за сегодня
        today_users = {
            user_id: user_data for user_id, user_data in users.items()
            if user_data['last_interaction'] and user_data['last_interaction'].date() == today
        }

        report = generate_report(today_users, "Анализ пользователей за сегодня", current_date)
        
        # Вывод в консоль
        print(report)

        # Сохранение отчета в файл
        report_dir = "reports"
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
        report_file = f"{report_dir}/user_analysis_today_{current_date}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"Отчет за сегодня сохранен в {report_file}")

        # Отправка в Telegram, если указано
        if send_to_telegram:
            await send_report_to_telegram(report)

        return report

    except Exception as e:
        report = f"Ошибка при анализе пользователей за сегодня: {str(e)}"
        logger.error(report)
        if send_to_telegram:
            await send_report_to_telegram(report)
        return report

async def analyze_users_all(send_to_telegram: bool = False) -> str:
    """Анализ всех данных пользователей"""
    try:
        logger.info("Начало анализа всех данных пользователей")
        db = Database()
        users = db.get_all_users()

        report = generate_report(users, "Анализ всех пользователей", current_date)
        
        # Вывод в консоль
        print(report)

        # Сохранение отчета в файл
        report_dir = "reports"
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
        report_file = f"{report_dir}/user_analysis_all_{current_date}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"Отчет всех пользователей сохранен в {report_file}")

        # Отправка в Telegram, если указано
        if send_to_telegram:
            await send_report_to_telegram(report)

        return report

    except Exception as e:
        report = f"Ошибка при анализе всех пользователей: {str(e)}"
        logger.error(report)
        if send_to_telegram:
            await send_report_to_telegram(report)
        return report

async def analyze_users_combined(send_to_telegram: bool = False) -> str:
    """Комбинированный анализ: за сегодня и за все время"""
    try:
        today_report = await analyze_users_today(send_to_telegram)
        all_report = await analyze_users_all(send_to_telegram)
        combined_report = f"{today_report}\n\n{all_report}"
        return combined_report
    except Exception as e:
        report = f"Ошибка при комбинированном анализе: {str(e)}"
        logger.error(report)
        if send_to_telegram:
            await send_report_to_telegram(report)
        return report

if __name__ == '__main__':
    import asyncio
    asyncio.run(analyze_users_combined())