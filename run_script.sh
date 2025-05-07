#!/bin/bash
# Активируем виртуальное окружение
source /home/server/Desktop/tg_bot/venv/bin/activate
# Запускаем Python-скрипт
python /home/server/Desktop/tg_bot/tg_bot.py
# Деактивируем виртуальное окружение
deactivate
