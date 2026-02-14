import os
import asyncio
import logging
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

# --- КАРТИНКИ И ОПИСАНИЯ (НОВЫЕ РАБОЧИЕ ССЫЛКИ) ---
images = {
    "1": {
        "url": "https://i.ibb.co/4TQB6z7/ash.jpg",
        "desc": "🔥 Пепел от костра\n\nВсё, что могло гореть — сгорело. Остался пепел и тишина.\nЭто не слабость. Это знак: пора остановиться.\nДаже в пепле хранится тепло — дайте себе время, и оно снова станет огнём."
    },
    "2": {
        "url": "https://i.ibb.co/BTKnP7y/battery.jpg",
        "desc": "🔋 Пустая батарея\n\nРабота на пределе — и вот индикатор показывает ноль.\nОрганизм просит паузы, а сознание всё ещё ищет розетку, которой нет.\nПодзарядка начинается не с дел, а с разрешения — не делать."
    },
    "3": {
        "url": "https://i.ibb.co/JxxYJ4z/rock.jpg",
        "desc": "🪨 Скалы и трещины\n\nМожно долго держать напряжение. Но даже камень даёт трещины.\nОни не делают его слабее. Они просто говорят: «Дальше так нельзя».\nПора сбавить давление и найти другую опору."
    },
    "4": {
        "url": "https://i.ibb.co/VLxgVyZ/sprout.jpg",
        "desc": "🌱 Возрождение ростка\n\nУсталость не навсегда.\nДаже когда кажется, что всё кончено — внутри уже пробивается жизнь.\nСначала робко. Потом смелее.\nВсё большое начинается с малого."
    }
}

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
    
    # Создаем медиа-группу с картинками
    media_group = []
    for k, v in images.items():
        media_group.append(InputMediaPhoto(media=v["url"]))
    
    # Отправляем все картинки одной группой
    await message.answer_media_group(media_group)
    
    # Небольшая пауза
    await asyncio.sleep(0.5)
    
    # Создаем кнопки для каждой картинки
    buttons = []
    for k in images.keys():
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

    await callback.message.answer(images[idx]["desc"])

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
