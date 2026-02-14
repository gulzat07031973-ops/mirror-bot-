import os
import asyncio
import logging
import base64
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# --- Токен бота из переменной окружения ---
TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    raise ValueError("No BOT_TOKEN environment variable set")

# --- КАРТИНКИ В ФОРМАТЕ BASE64 (встроены прямо в код) ---
images_base64 = {
    "1": {
        "data": "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",
        "desc": "🔥 Пепел от костра\n\nВсё, что могло гореть — сгорело. Остался пепел и тишина.\nЭто не слабость. Это знак: пора остановиться.\nДаже в пепле хранится тепло — дайте себе время, и оно снова станет огнём."
    },
    "2": {
        "data": "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",
        "desc": "🔋 Пустая батарея\n\nРабота на пределе — и вот индикатор показывает ноль.\nОрганизм просит паузы, а сознание всё ещё ищет розетку, которой нет.\nПодзарядка начинается не с дел, а с разрешения — не делать."
    },
    "3": {
        "data": "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",
        "desc": "🪨 Скалы и трещины\n\nМожно долго держать напряжение. Но даже камень даёт трещины.\nОни не делают его слабее. Они просто говорят: «Дальше так нельзя».\nПора сбавить давление и найти другую опору."
    },
    "4": {
        "data": "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",
        "desc": "🌱 Возрождение ростка\n\nУсталость не навсегда.\nДаже когда кажется, что всё кончено — внутри уже пробивается жизнь.\nСначала робко. Потом смелее.\nВсё большое начинается с малого."
    }
}

# --- Функция для декодирования base64 в InputMediaPhoto ---
def create_media_group():
    media_group = []
    for key, value in images_base64.items():
        # Декодируем base64 в байты
        image_data = base64.b64decode(value["data"])
        # Создаем InputMediaPhoto из байтов
        media_group.append(InputMediaPhoto(media=types.BufferedInputFile(image_data, filename=f"image_{key}.jpg")))
    return media_group

# --- Вопросы ---
questions = [
    "🧠 Вопрос 1: Где в теле вы ощущаете усталость или напряжение?",
    "💭 Вопрос 2: Какие мысли усиливают чувство выгорания?",
    "🌟 Вопрос 3: Что для вас действительно важно сейчас?",
    "🚶 Вопрос 4: Какой маленький шаг к восстановлению энергии вы можете сделать прямо сегодня?",
    "📌 Вопрос 5: Какой урок из этого опыта вы замечаете для будущих действий?"
]

# --- Хранилище ответов пользователей ---
user_data = {}

# --- Инициализация бота ---
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- Команда /start ---
@dp.message(Command("start"))
async def start(message: types.Message):
    # Отправляем приветствие
    await message.answer(
        "🔥 Добро пожаловать в демо-версию нейроигры «Зеркало»! 🔥\n\n"
        "Эта мини-игра поможет вам взглянуть на своё состояние через 4 образа и 5 вопросов.\n"
        "Выберите один образ, который откликается вам больше всего:"
    )
    
    # Небольшая пауза, чтобы сообщения не слиплись
    await asyncio.sleep(0.5)
    
    # Создаем медиа-группу с картинками из base64
    media_group = create_media_group()
    
    # Отправляем все картинки одной группой
    await message.answer_media_group(media_group)
    
    # Небольшая пауза
    await asyncio.sleep(0.5)
    
    # Создаем кнопки для каждой картинки
    buttons = []
    for k in images_base64.keys():
        buttons.append(InlineKeyboardButton(text=f"{k}️⃣", callback_data=f"img_{k}"))
    
    # Разбиваем на ряды по 2 кнопки
    keyboard = []
    for i in range(0, len(buttons), 2):
        keyboard.append(buttons[i:i+2])
    
    kb = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    # Отправляем сообщение с кнопками
    await message.answer("Нажмите на цифру выбранной картинки:", reply_markup=kb)

# --- Выбор картинки ---
@dp.callback_query(F.data.startswith("img_"))
async def on_image(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    idx = callback.data.split("_")[1]
    
    user_data[user_id] = {
        "chosen": idx, 
        "answers": [],
        "current_question": 0
    }

    await callback.message.answer(images_base64[idx]["desc"])

    # Кнопка для начала вопросов
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Начать вопросы", callback_data="start_questions")]
    ])
    await callback.message.answer("Готовы отвечать на вопросы?", reply_markup=kb)
    await callback.answer()

# --- Начало вопросов ---
@dp.callback_query(F.data == "start_questions")
async def start_questions(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {"answers": [], "current_question": 0}
    
    await ask_question(user_id, callback.message)
    await callback.answer()

async def ask_question(user_id: int, message: types.Message):
    if user_id not in user_data:
        user_data[user_id] = {"answers": [], "current_question": 0}
    
    q_index = user_data[user_id]["current_question"]
    
    if q_index < len(questions):
        await message.answer(questions[q_index])
        user_data[user_id]["awaiting_answer"] = True
    else:
        await show_results(user_id, message)

# --- Обработка текстовых ответов ---
@dp.message()
async def handle_answer(message: types.Message):
    user_id = message.from_user.id
    
    if user_id in user_data and user_data[user_id].get("awaiting_answer", False):
        user_data[user_id]["answers"].append(message.text)
        user_data[user_id]["current_question"] += 1
        user_data[user_id]["awaiting_answer"] = False
        
        await ask_question(user_id, message)
    else:
        await message.answer("Отправьте /start чтобы начать игру")

async def show_results(user_id: int, message: types.Message):
    answers = user_data[user_id].get("answers", [])
    
    result_text = "📝 **Ваши ответы:**\n\n"
    for i, answer in enumerate(answers):
        if i < len(questions):
            result_text += f"*{questions[i]}*\n_{answer}_\n\n"
    
    await message.answer(result_text, parse_mode="Markdown")
    
    await message.answer(
        "✨ **Спасибо! Вы прошли демо!** ✨\n\n"
        "Если вы хотите полную физическую версию игры — напишите мне в WhatsApp"
    )
    
    wa_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📱 Написать в WhatsApp",
            url="https://wa.me/77079898845?text=Я%20хочу%20купить%20игру%20«Зеркало»"
        )]
    ])
    await message.answer("Заказать полную версию:", reply_markup=wa_kb)

# --- Заглушка для порта (чтобы Render не падал) ---
async def health_check(request):
    return web.Response(text="Bot is running")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    logging.info("Web server started on port 8080")

async def main():
    # Запускаем веб-сервер (заглушка для Render)
    await start_web_server()
    
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
