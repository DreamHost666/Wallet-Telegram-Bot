# Ethereum Wallet Manager Bot

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Aiogram](https://img.shields.io/badge/Aiogram-2.x-blue.svg)](https://docs.aiogram.dev/)
[![Web3.py](https://img.shields.io/badge/Web3.py-5.x-green.svg)](https://web3py.readthedocs.io/)

Telegram-бот для безопасного управления Ethereum-кошельками с возможностью проверки баланса и хранения seed-фраз (BIP39).

## 🌟 Основные возможности

- 🏦 Проверка баланса ETH/USD по адресу кошелька
- 🔐 Шифрованное хранение seed-фраз (12/24 слова)
- 📋 Управление списком кошельков (добавление/удаление)
- 📊 История операций (в разработке)
- 🔄 Конвертация ETH → USD (через CoinGecko API)

## 📦 Требования

- Python 3.8+
- Aiogram 2.x
- Web3.py 5.x
- Infura API ключ

## 🛠 Установка

```bash
# Клонирование репозитория
git clone https://github.com/DreamHost666/Wallet-Telegram-Bot.git
cd Wallet-Telegram-Bot

# Установка зависимостей
pip install -r requirements.txt

# Настройка конфигурации
cp .env.example .env
```

⚙️ Конфигурация
Отредактируйте файл .env:

BOT_TOKEN=ваш_токен_от_BotFather
ADMIN_ID=ваш_telegram_id
INFURA_PROJECT_ID=ваш_infura_api_key
COINGECKO_API_KEY=ваш_api_ключ 

🚀 Запуск

```bash
python bot.py
```

🛡 Меры безопасности
🔒 Seed-фразы никогда не сохраняются в открытом виде

🚫 Бот никогда не запрашивает приватные ключи

📛 Все операции логируются (без чувствительных данных)

⚠️ Рекомендуется использовать только с тестовыми кошельками


📜 Лицензия
Подробнее в файле LICENSE.
