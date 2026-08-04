import os
import threading
import asyncio
import logging
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ---------- НАСТРОЙКИ ----------
API_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not API_TOKEN:
    raise ValueError("Переменная TELEGRAM_TOKEN не найдена!")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

user_data = {}

# ---------- ГЛАВНОЕ МЕНЮ (КАТЕГОРИИ) ----------
def get_categories_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("👁 Ресницы", callback_data="cat_lashes"),
        InlineKeyboardButton("👁 Брови", callback_data="cat_brows"),
        InlineKeyboardButton("💅 Маникюр", callback_data="cat_manicure"),
        InlineKeyboardButton("✂️ Стрижки", callback_data="cat_haircuts"),
        InlineKeyboardButton("🎨 Окрашивание волос", callback_data="cat_coloring"),
        InlineKeyboardButton("💎 Сложное окрашивание", callback_data="cat_complex"),
        InlineKeyboardButton("💆 Уход за волосами", callback_data="cat_care"),
        InlineKeyboardButton("🎓 Курсы", callback_data="cat_courses")
    )
    return keyboard

# ---------- МЕНЮ УСЛУГ ПО КАТЕГОРИЯМ ----------
def get_lashes_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🔄 Ламинирование/окрашивание (комплекс)", callback_data="service_lashes_complex"),
        InlineKeyboardButton("✨ Ламинирование ресниц", callback_data="service_lashes_lamination"),
        InlineKeyboardButton("🎨 Окрашивание ресниц", callback_data="service_lashes_color"),
        InlineKeyboardButton("📏 Ламинирование нижних ресниц", callback_data="service_lashes_bottom"),
        InlineKeyboardButton("🎨 Окрашивание нижних ресниц", callback_data="service_lashes_bottom_color"),
        InlineKeyboardButton("➕ Наращивание Классика", callback_data="service_lashes_classic"),
        InlineKeyboardButton("➕ Наращивание 2D", callback_data="service_lashes_2d"),
        InlineKeyboardButton("➕ Наращивание 3D", callback_data="service_lashes_3d"),
        InlineKeyboardButton("➕ Наращивание 4D+", callback_data="service_lashes_4d"),
        InlineKeyboardButton("🔧 Снятие чужих ресниц", callback_data="service_lashes_remove"),
        InlineKeyboardButton("🌈 Цветные ресницы", callback_data="service_lashes_colorful"),
        InlineKeyboardButton("🌀 Эффекты (изгиб М, L)", callback_data="service_lashes_effect"),
        InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")
    )
    return keyboard

def get_brows_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🔄 Окрашивание/коррекция (комплекс)", callback_data="service_brows_complex"),
        InlineKeyboardButton("🎨 Окрашивание бровей", callback_data="service_brows_color"),
        InlineKeyboardButton("🌿 Окрашивание бровей (хной)", callback_data="service_brows_henna"),
        InlineKeyboardButton("✂️ Коррекция (воск/пинцет)", callback_data="service_brows_correction"),
        InlineKeyboardButton("🔄 Ламинирование/окрашивание (комплекс)", callback_data="service_brows_lami_complex"),
        InlineKeyboardButton("✨ Ламинирование бровей", callback_data="service_brows_lamination"),
        InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")
    )
    return keyboard

def get_manicure_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("💅 Комплекс с покрытием", callback_data="service_manicure_complex"),
        InlineKeyboardButton("💅 Комплекс с гелевым покрытием", callback_data="service_manicure_gel"),
        InlineKeyboardButton("🧼 Гигиенический маникюр", callback_data="service_manicure_hygiene"),
        InlineKeyboardButton("👔 Мужской маникюр", callback_data="service_manicure_male"),
        InlineKeyboardButton("💊 С лечебным покрытием", callback_data="service_manicure_medical"),
        InlineKeyboardButton("📏 Наращивание ногтей", callback_data="service_manicure_extension"),
        InlineKeyboardButton("🔧 Ремонт ногтя", callback_data="service_manicure_repair"),
        InlineKeyboardButton("🎨 Простой дизайн", callback_data="service_manicure_design"),
        InlineKeyboardButton("🇫🇷 Френч", callback_data="service_manicure_french"),
        InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")
    )
    return keyboard

def get_haircuts_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("✂️ Женская стрижка", callback_data="service_haircut_women"),
        InlineKeyboardButton("✂️ Стрижка кончиков", callback_data="service_haircut_tips"),
        InlineKeyboardButton("✂️ Мужская стрижка", callback_data="service_haircut_men"),
        InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")
    )
    return keyboard

def get_coloring_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🎨 В один тон", callback_data="service_color_one"),
        InlineKeyboardButton("🎨 Сложное (седые)", callback_data="service_color_gray"),
        InlineKeyboardButton("🎨 Тонирование", callback_data="service_color_toning"),
        InlineKeyboardButton("🎨 Короткие волосы", callback_data="service_color_short"),
        InlineKeyboardButton("🎨 Длинные волосы", callback_data="service_color_long"),
        InlineKeyboardButton("💨 Мытье + сушка (брашинг)", callback_data="service_color_brushing"),
        InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")
    )
    return keyboard

def get_complex_coloring_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("💎 Мелирование/Шатуш", callback_data="service_complex_highlight"),
        InlineKeyboardButton("💎 Балаяж", callback_data="service_complex_balayage"),
        InlineKeyboardButton("💎 Омбре/Сомбре", callback_data="service_complex_ombre"),
        InlineKeyboardButton("💎 Колорирование (2-3 цв)", callback_data="service_complex_colorization"),
        InlineKeyboardButton("💎 AirTouch", callback_data="service_complex_airtouch"),
        InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")
    )
    return keyboard

def get_care_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("💧 Hydration Boost (увлажнение)", callback_data="service_care_hydration"),
        InlineKeyboardButton("🔧 Repair Ritual (восстановление)", callback_data="service_care_repair"),
        InlineKeyboardButton("⚖️ Scalp Balance (кожа головы)", callback_data="service_care_scalp"),
        InlineKeyboardButton("💨 Volume Therapy (объем)", callback_data="service_care_volume"),
        InlineKeyboardButton("⚡ Express Moroccanoil (экспресс)", callback_data="service_care_express"),
        InlineKeyboardButton("✨ Smooth & Shine (разглаживание)", callback_data="service_care_smooth"),
        InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")
    )
    return keyboard

def get_courses_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📚 Базовый курс маникюра", callback_data="service_course_base"),
        InlineKeyboardButton("📚 Повышение квалификации", callback_data="service_course_advanced"),
        InlineKeyboardButton("📚 Комбо (базовый+повышение)", callback_data="service_course_combo"),
        InlineKeyboardButton("📚 Комбо ЭКСПРЕСС", callback_data="service_course_express"),
        InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")
    )
    return keyboard

# ---------- КНОПКИ ВРЕМЕНИ (10:00 - 22:00, шаг 30 мин) ----------
def get_time_buttons():
    keyboard = InlineKeyboardMarkup(row_width=4)
    keyboard.add(
        InlineKeyboardButton("10:00", callback_data="time_10:00"),
        InlineKeyboardButton("10:30", callback_data="time_10:30"),
        InlineKeyboardButton("11:00", callback_data="time_11:00"),
        InlineKeyboardButton("11:30", callback_data="time_11:30"),
        InlineKeyboardButton("12:00", callback_data="time_12:00"),
        InlineKeyboardButton("12:30", callback_data="time_12:30"),
        InlineKeyboardButton("13:00", callback_data="time_13:00"),
        InlineKeyboardButton("13:30", callback_data="time_13:30"),
        InlineKeyboardButton("14:00", callback_data="time_14:00"),
        InlineKeyboardButton("14:30", callback_data="time_14:30"),
        InlineKeyboardButton("15:00", callback_data="time_15:00"),
        InlineKeyboardButton("15:30", callback_data="time_15:30"),
        InlineKeyboardButton("16:00", callback_data="time_16:00"),
        InlineKeyboardButton("16:30", callback_data="time_16:30"),
        InlineKeyboardButton("17:00", callback_data="time_17:00"),
        InlineKeyboardButton("17:30", callback_data="time_17:30"),
        InlineKeyboardButton("18:00", callback_data="time_18:00"),
        InlineKeyboardButton("18:30", callback_data="time_18:30"),
        InlineKeyboardButton("19:00", callback_data="time_19:00"),
        InlineKeyboardButton("19:30", callback_data="time_19:30"),
        InlineKeyboardButton("20:00", callback_data="time_20:00"),
        InlineKeyboardButton("20:30", callback_data="time_20:30"),
        InlineKeyboardButton("21:00", callback_data="time_21:00"),
        InlineKeyboardButton("21:30", callback_data="time_21:30")
    )
    keyboard.add(InlineKeyboardButton("⬅️ Назад к услугам", callback_data="back_to_category"))
    return keyboard

# ---------- КОМАНДА /START ----------
@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_data[message.from_user.id] = {}
    await message.answer(
        "👋 Добро пожаловать в BeautyLoftStudio!\n"
        "Выберите категорию услуг:",
        reply_markup=get_categories_menu()
    )

# ---------- ОБРАБОТКА КАТЕГОРИЙ ----------
@dp.callback_query(lambda c: c.data.startswith('cat_'))
async def process_category(callback_query: types.CallbackQuery):
    category = callback_query.data.replace('cat_', '')
    user_data[callback_query.from_user.id]['category'] = category
    
    menus = {
        'lashes': get_lashes_menu,
        'brows': get_brows_menu,
        'manicure': get_manicure_menu,
        'haircuts': get_haircuts_menu,
        'coloring': get_coloring_menu,
        'complex': get_complex_coloring_menu,
        'care': get_care_menu,
        'courses': get_courses_menu
    }
    
    category_names = {
        'lashes': '👁 Ресницы',
        'brows': '👁 Брови',
        'manicure': '💅 Маникюр',
        'haircuts': '✂️ Стрижки',
        'coloring': '🎨 Окрашивание волос',
        'complex': '💎 Сложное окрашивание',
        'care': '💆 Уход за волосами',
        'courses': '🎓 Курсы'
    }
    
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        f"📋 {category_names.get(category, 'Услуги')}:\nВыберите конкретную услугу:",
        reply_markup=menus.get(category, get_categories_menu)()
    )

# ---------- ОБРАБОТКА ВЫБОРА УСЛУГИ ----------
@dp.callback_query(lambda c: c.data.startswith('service_'))
async def process_service(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    service_code = callback_query.data
    
    # Красивые названия для вывода
    service_names = {
        # Ресницы
        'service_lashes_complex': 'Ламинирование/окрашивание ресниц (комплекс)',
        'service_lashes_lamination': 'Ламинирование ресниц',
        'service_lashes_color': 'Окрашивание ресниц',
        'service_lashes_bottom': 'Ламинирование нижних ресниц',
        'service_lashes_bottom_color': 'Окрашивание нижних ресниц',
        'service_lashes_classic': 'Наращивание Классика',
        'service_lashes_2d': 'Наращивание 2D',
        'service_lashes_3d': 'Наращивание 3D',
        'service_lashes_4d': 'Наращивание 4D+',
        'service_lashes_remove': 'Снятие чужих ресниц',
        'service_lashes_colorful': 'Цветные ресницы',
        'service_lashes_effect': 'Эффекты (изгиб М, L)',
        # Брови
        'service_brows_complex': 'Окрашивание/коррекция бровей (комплекс)',
        'service_brows_color': 'Окрашивание бровей',
        'service_brows_henna': 'Окрашивание бровей (хной)',
        'service_brows_correction': 'Коррекция бровей (воск/пинцет)',
        'service_brows_lami_complex': 'Ламинирование/окрашивание бровей (комплекс)',
        'service_brows_lamination': 'Ламинирование бровей',
        # Маникюр
        'service_manicure_complex': 'Комплекс маникюра с покрытием',
        'service_manicure_gel': 'Комплекс маникюра с гелевым покрытием',
        'service_manicure_hygiene': 'Гигиенический маникюр',
        'service_manicure_male': 'Мужской маникюр',
        'service_manicure_medical': 'Маникюр с лечебным покрытием',
        'service_manicure_extension': 'Наращивание ногтей',
        'service_manicure_repair': 'Ремонт ногтя',
        'service_manicure_design': 'Простой дизайн',
        'service_manicure_french': 'Френч',
        # Стрижки
        'service_haircut_women': 'Женская стрижка',
        'service_haircut_tips': 'Стрижка кончиков',
        'service_haircut_men': 'Мужская стрижка',
        # Окрашивание волос
        'service_color_one': 'Окрашивание в один тон',
        'service_color_gray': 'Окрашивание (седые волосы)',
        'service_color_toning': 'Тонирование волос',
        'service_color_short': 'Окрашивание (короткие)',
        'service_color_long': 'Окрашивание (длинные)',
        'service_color_brushing': 'Мытье + сушка (брашинг)',
        # Сложное окрашивание
        'service_complex_highlight': 'Мелирование/Шатуш',
        'service_complex_balayage': 'Балаяж',
        'service_complex_ombre': 'Омбре/Сомбре',
        'service_complex_colorization': 'Колорирование (2-3 цв)',
        'service_complex_airtouch': 'AirTouch',
        # Уход
        'service_care_hydration': 'Hydration Boost (увлажнение)',
        'service_care_repair': 'Repair Ritual (восстановление)',
        'service_care_scalp': 'Scalp Balance (кожа головы)',
        'service_care_volume': 'Volume Therapy (объем)',
        'service_care_express': 'Express Moroccanoil (экспресс)',
        'service_care_smooth': 'Smooth & Shine (разглаживание)',
        # Курсы
        'service_course_base': 'Базовый курс маникюра',
        'service_course_advanced': 'Повышение квалификации',
        'service_course_combo': 'Комбо (базовый+повышение)',
        'service_course_express': 'Комбо ЭКСПРЕСС'
    }
    
    service_name = service_names.get(service_code, 'Услуга')
    
    await bot.answer_callback_query(callback_query.id)
    
    # Сохраняем в данные пользователя
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['service'] = service_name
    
    await bot.send_message(
        user_id,
        f"✅ Вы выбрали: *{service_name}*\n\n"
        f"Теперь выберите удобное время:",
        parse_mode="Markdown",
        reply_markup=get_time_buttons()
    )

# ---------- ОБРАБОТКА ВРЕМЕНИ ----------
@dp.callback_query(lambda c: c.data.startswith('time_'))
async def process_time(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    time_slot = callback_query.data.replace('time_', '')
    service = user_data.get(user_id, {}).get('service', 'Услуга')
    
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        user_id,
        f"✅ *Запись создана!*\n\n"
        f"📌 Услуга: {service}\n"
        f"⏰ Время: {time_slot}\n\n"
        f"Скоро администратор подтвердит запись.",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardRemove()
    )
    
    # Уведомление администратору
    admin_id = 123456789  # ← ВСТАВЬТЕ ВАШ ID (узнать через @userinfobot)
    await bot.send_message(
        admin_id,
        f"🔔 *НОВАЯ ЗАПИСЬ!*\n"
        f"Клиент: @{callback_query.from_user.username or 'без юзернейма'}\n"
        f"Услуга: {service}\n"
        f"Время: {time_slot}",
        parse_mode="Markdown"
    )

# ---------- КНОПКИ НАЗАД ----------
@dp.callback_query(lambda c: c.data == "back_to_categories")
async def back_to_categories(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        "👋 Выберите категорию услуг:",
        reply_markup=get_categories_menu()
    )

@dp.callback_query(lambda c: c.data == "back_to_category")
async def back_to_category(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    category = user_data.get(user_id, {}).get('category', 'lashes')
    
    menus = {
        'lashes': get_lashes_menu,
        'brows': get_brows_menu,
        'manicure': get_manicure_menu,
        'haircuts': get_haircuts_menu,
        'coloring': get_coloring_menu,
        'complex': get_complex_coloring_menu,
        'care': get_care_menu,
        'courses': get_courses_menu
    }
    
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        "📋 Выберите услугу:",
        reply_markup=menus.get(category, get_categories_menu)()
    )

# ---------- ЗАПУСК БОТА И ВЕБ-СЕРВЕРА ----------
def run_bot():
    asyncio.run(dp.start_polling(bot))

@app.route('/')
def hello():
    return "🤖 BeautyLoftStudio Bot is running!"

@app.route('/health')
def health():
    return "OK"

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
EOFcat > app.py << 'EOF'
import os
import threading
import asyncio
import logging
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ---------- НАСТРОЙКИ ----------
API_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not API_TOKEN:
    raise ValueError("Переменная TELEGRAM_TOKEN не найдена!")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

user_data = {}

# ---------- ГЛАВНОЕ МЕНЮ (КАТЕГОРИИ) ----------
def get_categories_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("👁 Ресницы", callback_data="cat_lashes"),
        InlineKeyboardButton("👁 Брови", callback_data="cat_brows"),
        InlineKeyboardButton("💅 Маникюр", callback_data="cat_manicure"),
        InlineKeyboardButton("✂️ Стрижки", callback_data="cat_haircuts"),
        InlineKeyboardButton("🎨 Окрашивание волос", callback_data="cat_coloring"),
        InlineKeyboardButton("💎 Сложное окрашивание", callback_data="cat_complex"),
        InlineKeyboardButton("💆 Уход за волосами", callback_data="cat_care"),
        InlineKeyboardButton("🎓 Курсы", callback_data="cat_courses")
    )
    return keyboard

# ---------- МЕНЮ УСЛУГ ПО КАТЕГОРИЯМ ----------
def get_lashes_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🔄 Ламинирование/окрашивание (комплекс)", callback_data="service_lashes_complex"),
        InlineKeyboardButton("✨ Ламинирование ресниц", callback_data="service_lashes_lamination"),
        InlineKeyboardButton("🎨 Окрашивание ресниц", callback_data="service_lashes_color"),
        InlineKeyboardButton("📏 Ламинирование нижних ресниц", callback_data="service_lashes_bottom"),
        InlineKeyboardButton("🎨 Окрашивание нижних ресниц", callback_data="service_lashes_bottom_color"),
        InlineKeyboardButton("➕ Наращивание Классика", callback_data="service_lashes_classic"),
        InlineKeyboardButton("➕ Наращивание 2D", callback_data="service_lashes_2d"),
        InlineKeyboardButton("➕ Наращивание 3D", callback_data="service_lashes_3d"),
        InlineKeyboardButton("➕ Наращивание 4D+", callback_data="service_lashes_4d"),
        InlineKeyboardButton("🔧 Снятие чужих ресниц", callback_data="service_lashes_remove"),
        InlineKeyboardButton("🌈 Цветные ресницы", callback_data="service_lashes_colorful"),
        InlineKeyboardButton("🌀 Эффекты (изгиб М, L)", callback_data="service_lashes_effect"),
        InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")
    )
    return keyboard

def get_brows_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🔄 Окрашивание/коррекция (комплекс)", callback_data="service_brows_complex"),
        InlineKeyboardButton("🎨 Окрашивание бровей", callback_data="service_brows_color"),
        InlineKeyboardButton("🌿 Окрашивание бровей (хной)", callback_data="service_brows_henna"),
        InlineKeyboardButton("✂️ Коррекция (воск/пинцет)", callback_data="service_brows_correction"),
        InlineKeyboardButton("🔄 Ламинирование/окрашивание (комплекс)", callback_data="service_brows_lami_complex"),
        InlineKeyboardButton("✨ Ламинирование бровей", callback_data="service_brows_lamination"),
        InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")
    )
    return keyboard

def get_manicure_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("💅 Комплекс с покрытием", callback_data="service_manicure_complex"),
        InlineKeyboardButton("💅 Комплекс с гелевым покрытием", callback_data="service_manicure_gel"),
        InlineKeyboardButton("🧼 Гигиенический маникюр", callback_data="service_manicure_hygiene"),
        InlineKeyboardButton("👔 Мужской маникюр", callback_data="service_manicure_male"),
        InlineKeyboardButton("💊 С лечебным покрытием", callback_data="service_manicure_medical"),
        InlineKeyboardButton("📏 Наращивание ногтей", callback_data="service_manicure_extension"),
        InlineKeyboardButton("🔧 Ремонт ногтя", callback_data="service_manicure_repair"),
        InlineKeyboardButton("🎨 Простой дизайн", callback_data="service_manicure_design"),
        InlineKeyboardButton("🇫🇷 Френч", callback_data="service_manicure_french"),
        InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")
    )
    return keyboard

def get_haircuts_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("✂️ Женская стрижка", callback_data="service_haircut_women"),
        InlineKeyboardButton("✂️ Стрижка кончиков", callback_data="service_haircut_tips"),
        InlineKeyboardButton("✂️ Мужская стрижка", callback_data="service_haircut_men"),
        InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")
    )
    return keyboard

def get_coloring_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🎨 В один тон", callback_data="service_color_one"),
        InlineKeyboardButton("🎨 Сложное (седые)", callback_data="service_color_gray"),
        InlineKeyboardButton("🎨 Тонирование", callback_data="service_color_toning"),
        InlineKeyboardButton("🎨 Короткие волосы", callback_data="service_color_short"),
        InlineKeyboardButton("🎨 Длинные волосы", callback_data="service_color_long"),
        InlineKeyboardButton("💨 Мытье + сушка (брашинг)", callback_data="service_color_brushing"),
        InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")
    )
    return keyboard

def get_complex_coloring_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("💎 Мелирование/Шатуш", callback_data="service_complex_highlight"),
        InlineKeyboardButton("💎 Балаяж", callback_data="service_complex_balayage"),
        InlineKeyboardButton("💎 Омбре/Сомбре", callback_data="service_complex_ombre"),
        InlineKeyboardButton("💎 Колорирование (2-3 цв)", callback_data="service_complex_colorization"),
        InlineKeyboardButton("💎 AirTouch", callback_data="service_complex_airtouch"),
        InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")
    )
    return keyboard

def get_care_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("💧 Hydration Boost (увлажнение)", callback_data="service_care_hydration"),
        InlineKeyboardButton("🔧 Repair Ritual (восстановление)", callback_data="service_care_repair"),
        InlineKeyboardButton("⚖️ Scalp Balance (кожа головы)", callback_data="service_care_scalp"),
        InlineKeyboardButton("💨 Volume Therapy (объем)", callback_data="service_care_volume"),
        InlineKeyboardButton("⚡ Express Moroccanoil (экспресс)", callback_data="service_care_express"),
        InlineKeyboardButton("✨ Smooth & Shine (разглаживание)", callback_data="service_care_smooth"),
        InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")
    )
    return keyboard

def get_courses_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📚 Базовый курс маникюра", callback_data="service_course_base"),
        InlineKeyboardButton("📚 Повышение квалификации", callback_data="service_course_advanced"),
        InlineKeyboardButton("📚 Комбо (базовый+повышение)", callback_data="service_course_combo"),
        InlineKeyboardButton("📚 Комбо ЭКСПРЕСС", callback_data="service_course_express"),
        InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")
    )
    return keyboard

# ---------- КНОПКИ ВРЕМЕНИ (10:00 - 22:00, шаг 30 мин) ----------
def get_time_buttons():
    keyboard = InlineKeyboardMarkup(row_width=4)
    keyboard.add(
        InlineKeyboardButton("10:00", callback_data="time_10:00"),
        InlineKeyboardButton("10:30", callback_data="time_10:30"),
        InlineKeyboardButton("11:00", callback_data="time_11:00"),
        InlineKeyboardButton("11:30", callback_data="time_11:30"),
        InlineKeyboardButton("12:00", callback_data="time_12:00"),
        InlineKeyboardButton("12:30", callback_data="time_12:30"),
        InlineKeyboardButton("13:00", callback_data="time_13:00"),
        InlineKeyboardButton("13:30", callback_data="time_13:30"),
        InlineKeyboardButton("14:00", callback_data="time_14:00"),
        InlineKeyboardButton("14:30", callback_data="time_14:30"),
        InlineKeyboardButton("15:00", callback_data="time_15:00"),
        InlineKeyboardButton("15:30", callback_data="time_15:30"),
        InlineKeyboardButton("16:00", callback_data="time_16:00"),
        InlineKeyboardButton("16:30", callback_data="time_16:30"),
        InlineKeyboardButton("17:00", callback_data="time_17:00"),
        InlineKeyboardButton("17:30", callback_data="time_17:30"),
        InlineKeyboardButton("18:00", callback_data="time_18:00"),
        InlineKeyboardButton("18:30", callback_data="time_18:30"),
        InlineKeyboardButton("19:00", callback_data="time_19:00"),
        InlineKeyboardButton("19:30", callback_data="time_19:30"),
        InlineKeyboardButton("20:00", callback_data="time_20:00"),
        InlineKeyboardButton("20:30", callback_data="time_20:30"),
        InlineKeyboardButton("21:00", callback_data="time_21:00"),
        InlineKeyboardButton("21:30", callback_data="time_21:30")
    )
    keyboard.add(InlineKeyboardButton("⬅️ Назад к услугам", callback_data="back_to_category"))
    return keyboard

# ---------- КОМАНДА /START ----------
@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_data[message.from_user.id] = {}
    await message.answer(
        "👋 Добро пожаловать в BeautyLoftStudio!\n"
        "Выберите категорию услуг:",
        reply_markup=get_categories_menu()
    )

# ---------- ОБРАБОТКА КАТЕГОРИЙ ----------
@dp.callback_query(lambda c: c.data.startswith('cat_'))
async def process_category(callback_query: types.CallbackQuery):
    category = callback_query.data.replace('cat_', '')
    user_data[callback_query.from_user.id]['category'] = category
    
    menus = {
        'lashes': get_lashes_menu,
        'brows': get_brows_menu,
        'manicure': get_manicure_menu,
        'haircuts': get_haircuts_menu,
        'coloring': get_coloring_menu,
        'complex': get_complex_coloring_menu,
        'care': get_care_menu,
        'courses': get_courses_menu
    }
    
    category_names = {
        'lashes': '👁 Ресницы',
        'brows': '👁 Брови',
        'manicure': '💅 Маникюр',
        'haircuts': '✂️ Стрижки',
        'coloring': '🎨 Окрашивание волос',
        'complex': '💎 Сложное окрашивание',
        'care': '💆 Уход за волосами',
        'courses': '🎓 Курсы'
    }
    
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        f"📋 {category_names.get(category, 'Услуги')}:\nВыберите конкретную услугу:",
        reply_markup=menus.get(category, get_categories_menu)()
    )

# ---------- ОБРАБОТКА ВЫБОРА УСЛУГИ ----------
@dp.callback_query(lambda c: c.data.startswith('service_'))
async def process_service(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    service_code = callback_query.data
    
    # Красивые названия для вывода
    service_names = {
        # Ресницы
        'service_lashes_complex': 'Ламинирование/окрашивание ресниц (комплекс)',
        'service_lashes_lamination': 'Ламинирование ресниц',
        'service_lashes_color': 'Окрашивание ресниц',
        'service_lashes_bottom': 'Ламинирование нижних ресниц',
        'service_lashes_bottom_color': 'Окрашивание нижних ресниц',
        'service_lashes_classic': 'Наращивание Классика',
        'service_lashes_2d': 'Наращивание 2D',
        'service_lashes_3d': 'Наращивание 3D',
        'service_lashes_4d': 'Наращивание 4D+',
        'service_lashes_remove': 'Снятие чужих ресниц',
        'service_lashes_colorful': 'Цветные ресницы',
        'service_lashes_effect': 'Эффекты (изгиб М, L)',
        # Брови
        'service_brows_complex': 'Окрашивание/коррекция бровей (комплекс)',
        'service_brows_color': 'Окрашивание бровей',
        'service_brows_henna': 'Окрашивание бровей (хной)',
        'service_brows_correction': 'Коррекция бровей (воск/пинцет)',
        'service_brows_lami_complex': 'Ламинирование/окрашивание бровей (комплекс)',
        'service_brows_lamination': 'Ламинирование бровей',
        # Маникюр
        'service_manicure_complex': 'Комплекс маникюра с покрытием',
        'service_manicure_gel': 'Комплекс маникюра с гелевым покрытием',
        'service_manicure_hygiene': 'Гигиенический маникюр',
        'service_manicure_male': 'Мужской маникюр',
        'service_manicure_medical': 'Маникюр с лечебным покрытием',
        'service_manicure_extension': 'Наращивание ногтей',
        'service_manicure_repair': 'Ремонт ногтя',
        'service_manicure_design': 'Простой дизайн',
        'service_manicure_french': 'Френч',
        # Стрижки
        'service_haircut_women': 'Женская стрижка',
        'service_haircut_tips': 'Стрижка кончиков',
        'service_haircut_men': 'Мужская стрижка',
        # Окрашивание волос
        'service_color_one': 'Окрашивание в один тон',
        'service_color_gray': 'Окрашивание (седые волосы)',
        'service_color_toning': 'Тонирование волос',
        'service_color_short': 'Окрашивание (короткие)',
        'service_color_long': 'Окрашивание (длинные)',
        'service_color_brushing': 'Мытье + сушка (брашинг)',
        # Сложное окрашивание
        'service_complex_highlight': 'Мелирование/Шатуш',
        'service_complex_balayage': 'Балаяж',
        'service_complex_ombre': 'Омбре/Сомбре',
        'service_complex_colorization': 'Колорирование (2-3 цв)',
        'service_complex_airtouch': 'AirTouch',
        # Уход
        'service_care_hydration': 'Hydration Boost (увлажнение)',
        'service_care_repair': 'Repair Ritual (восстановление)',
        'service_care_scalp': 'Scalp Balance (кожа головы)',
        'service_care_volume': 'Volume Therapy (объем)',
        'service_care_express': 'Express Moroccanoil (экспресс)',
        'service_care_smooth': 'Smooth & Shine (разглаживание)',
        # Курсы
        'service_course_base': 'Базовый курс маникюра',
        'service_course_advanced': 'Повышение квалификации',
        'service_course_combo': 'Комбо (базовый+повышение)',
        'service_course_express': 'Комбо ЭКСПРЕСС'
    }
    
    service_name = service_names.get(service_code, 'Услуга')
    
    await bot.answer_callback_query(callback_query.id)
    
    # Сохраняем в данные пользователя
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['service'] = service_name
    
    await bot.send_message(
        user_id,
        f"✅ Вы выбрали: *{service_name}*\n\n"
        f"Теперь выберите удобное время:",
        parse_mode="Markdown",
        reply_markup=get_time_buttons()
    )

# ---------- ОБРАБОТКА ВРЕМЕНИ ----------
@dp.callback_query(lambda c: c.data.startswith('time_'))
async def process_time(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    time_slot = callback_query.data.replace('time_', '')
    service = user_data.get(user_id, {}).get('service', 'Услуга')
    
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        user_id,
        f"✅ *Запись создана!*\n\n"
        f"📌 Услуга: {service}\n"
        f"⏰ Время: {time_slot}\n\n"
        f"Скоро администратор подтвердит запись.",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardRemove()
    )
    
    # Уведомление администратору
    admin_id = 742585100  # ← ВСТАВЬТЕ ВАШ ID (узнать через @userinfobot)
    await bot.send_message(
        admin_id,
        f"🔔 *НОВАЯ ЗАПИСЬ!*\n"
        f"Клиент: @{callback_query.from_user.username or 'без юзернейма'}\n"
        f"Услуга: {service}\n"
        f"Время: {time_slot}",
        parse_mode="Markdown"
    )

# ---------- КНОПКИ НАЗАД ----------
@dp.callback_query(lambda c: c.data == "back_to_categories")
async def back_to_categories(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        "👋 Выберите категорию услуг:",
        reply_markup=get_categories_menu()
    )

@dp.callback_query(lambda c: c.data == "back_to_category")
async def back_to_category(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    category = user_data.get(user_id, {}).get('category', 'lashes')
    
    menus = {
        'lashes': get_lashes_menu,
        'brows': get_brows_menu,
        'manicure': get_manicure_menu,
        'haircuts': get_haircuts_menu,
        'coloring': get_coloring_menu,
        'complex': get_complex_coloring_menu,
        'care': get_care_menu,
        'courses': get_courses_menu
    }
    
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        "📋 Выберите услугу:",
        reply_markup=menus.get(category, get_categories_menu)()
    )

# ---------- ЗАПУСК БОТА И ВЕБ-СЕРВЕРА ----------
def run_bot():
    asyncio.run(dp.start_polling(bot))

@app.route('/')
def hello():
    return "🤖 BeautyLoftStudio Bot is running!"

@app.route('/health')
def health():
    return "OK"

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
EOFcat > app.py << 'EOF'
import os
import threading
import asyncio
import logging
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ---------- НАСТРОЙКИ ----------
API_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not API_TOKEN:
    raise ValueError("Переменная TELEGRAM_TOKEN не найдена!")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

user_data = {}

# ---------- ГЛАВНОЕ МЕНЮ (КАТЕГОРИИ) ----------
def get_categories_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("👁 Ресницы", callback_data="cat_lashes"),
        InlineKeyboardButton("👁 Брови", callback_data="cat_brows"),
        InlineKeyboardButton("💅 Маникюр", callback_data="cat_manicure"),
        InlineKeyboardButton("✂️ Стрижки", callback_data="cat_haircuts"),
        InlineKeyboardButton("🎨 Окрашивание волос", callback_data="cat_coloring"),
        InlineKeyboardButton("💎 Сложное окрашивание", callback_data="cat_complex"),
        InlineKeyboardButton("💆 Уход за волосами", callback_data="cat_care"),
        InlineKeyboardButton("🎓 Курсы", callback_data="cat_courses")
    )
    return keyboard

# ---------- МЕНЮ УСЛУГ ПО КАТЕГОРИЯМ ----------
def get_lashes_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🔄 Ламинирование/окрашивание (комплекс)", callback_data="service_lashes_complex"),
        InlineKeyboardButton("✨ Ламинирование ресниц", callback_data="service_lashes_lamination"),
        InlineKeyboardButton("🎨 Окрашивание ресниц", callback_data="service_lashes_color"),
        InlineKeyboardButton("📏 Ламинирование нижних ресниц", callback_data="service_lashes_bottom"),
        InlineKeyboardButton("🎨 Окрашивание нижних ресниц", callback_data="service_lashes_bottom_color"),
        InlineKeyboardButton("➕ Наращивание Классика", callback_data="service_lashes_classic"),
        InlineKeyboardButton("➕ Наращивание 2D", callback_data="service_lashes_2d"),
        InlineKeyboardButton("➕ Наращивание 3D", callback_data="service_lashes_3d"),
        InlineKeyboardButton("➕ Наращивание 4D+", callback_data="service_lashes_4d"),
        InlineKeyboardButton("🔧 Снятие чужих ресниц", callback_data="service_lashes_remove"),
        InlineKeyboardButton("🌈 Цветные ресницы", callback_data="service_lashes_colorful"),
        InlineKeyboardButton("🌀 Эффекты (изгиб М, L)", callback_data="service_lashes_effect"),
        InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")
    )
    return keyboard

def get_brows_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🔄 Окрашивание/коррекция (комплекс)", callback_data="service_brows_complex"),
        InlineKeyboardButton("🎨 Окрашивание бровей", callback_data="service_brows_color"),
        InlineKeyboardButton("🌿 Окрашивание бровей (хной)", callback_data="service_brows_henna"),
        InlineKeyboardButton("✂️ Коррекция (воск/пинцет)", callback_data="service_brows_correction"),
        InlineKeyboardButton("🔄 Ламинирование/окрашивание (комплекс)", callback_data="service_brows_lami_complex"),
        InlineKeyboardButton("✨ Ламинирование бровей", callback_data="service_brows_lamination"),
        InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")
    )
    return keyboard

def get_manicure_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("💅 Комплекс с покрытием", callback_data="service_manicure_complex"),
        InlineKeyboardButton("💅 Комплекс с гелевым покрытием", callback_data="service_manicure_gel"),
        InlineKeyboardButton("🧼 Гигиенический маникюр", callback_data="service_manicure_hygiene"),
        InlineKeyboardButton("👔 Мужской маникюр", callback_data="service_manicure_male"),
        InlineKeyboardButton("💊 С лечебным покрытием", callback_data="service_manicure_medical"),
        InlineKeyboardButton("📏 Наращивание ногтей", callback_data="service_manicure_extension"),
        InlineKeyboardButton("🔧 Ремонт ногтя", callback_data="service_manicure_repair"),
        InlineKeyboardButton("🎨 Простой дизайн", callback_data="service_manicure_design"),
        InlineKeyboardButton("🇫🇷 Френч", callback_data="service_manicure_french"),
        InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")
    )
    return keyboard

def get_haircuts_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("✂️ Женская стрижка", callback_data="service_haircut_women"),
        InlineKeyboardButton("✂️ Стрижка кончиков", callback_data="service_haircut_tips"),
        InlineKeyboardButton("✂️ Мужская стрижка", callback_data="service_haircut_men"),
        InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")
    )
    return keyboard

def get_coloring_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🎨 В один тон", callback_data="service_color_one"),
        InlineKeyboardButton("🎨 Сложное (седые)", callback_data="service_color_gray"),
        InlineKeyboardButton("🎨 Тонирование", callback_data="service_color_toning"),
        InlineKeyboardButton("🎨 Короткие волосы", callback_data="service_color_short"),
        InlineKeyboardButton("🎨 Длинные волосы", callback_data="service_color_long"),
        InlineKeyboardButton("💨 Мытье + сушка (брашинг)", callback_data="service_color_brushing"),
        InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")
    )
    return keyboard

def get_complex_coloring_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("💎 Мелирование/Шатуш", callback_data="service_complex_highlight"),
        InlineKeyboardButton("💎 Балаяж", callback_data="service_complex_balayage"),
        InlineKeyboardButton("💎 Омбре/Сомбре", callback_data="service_complex_ombre"),
        InlineKeyboardButton("💎 Колорирование (2-3 цв)", callback_data="service_complex_colorization"),
        InlineKeyboardButton("💎 AirTouch", callback_data="service_complex_airtouch"),
        InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")
    )
    return keyboard

def get_care_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("💧 Hydration Boost (увлажнение)", callback_data="service_care_hydration"),
        InlineKeyboardButton("🔧 Repair Ritual (восстановление)", callback_data="service_care_repair"),
        InlineKeyboardButton("⚖️ Scalp Balance (кожа головы)", callback_data="service_care_scalp"),
        InlineKeyboardButton("💨 Volume Therapy (объем)", callback_data="service_care_volume"),
        InlineKeyboardButton("⚡ Express Moroccanoil (экспресс)", callback_data="service_care_express"),
        InlineKeyboardButton("✨ Smooth & Shine (разглаживание)", callback_data="service_care_smooth"),
        InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")
    )
    return keyboard

def get_courses_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📚 Базовый курс маникюра", callback_data="service_course_base"),
        InlineKeyboardButton("📚 Повышение квалификации", callback_data="service_course_advanced"),
        InlineKeyboardButton("📚 Комбо (базовый+повышение)", callback_data="service_course_combo"),
        InlineKeyboardButton("📚 Комбо ЭКСПРЕСС", callback_data="service_course_express"),
        InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")
    )
    return keyboard

# ---------- КНОПКИ ВРЕМЕНИ (10:00 - 22:00, шаг 30 мин) ----------
def get_time_buttons():
    keyboard = InlineKeyboardMarkup(row_width=4)
    keyboard.add(
        InlineKeyboardButton("10:00", callback_data="time_10:00"),
        InlineKeyboardButton("10:30", callback_data="time_10:30"),
        InlineKeyboardButton("11:00", callback_data="time_11:00"),
        InlineKeyboardButton("11:30", callback_data="time_11:30"),
        InlineKeyboardButton("12:00", callback_data="time_12:00"),
        InlineKeyboardButton("12:30", callback_data="time_12:30"),
        InlineKeyboardButton("13:00", callback_data="time_13:00"),
        InlineKeyboardButton("13:30", callback_data="time_13:30"),
        InlineKeyboardButton("14:00", callback_data="time_14:00"),
        InlineKeyboardButton("14:30", callback_data="time_14:30"),
        InlineKeyboardButton("15:00", callback_data="time_15:00"),
        InlineKeyboardButton("15:30", callback_data="time_15:30"),
        InlineKeyboardButton("16:00", callback_data="time_16:00"),
        InlineKeyboardButton("16:30", callback_data="time_16:30"),
        InlineKeyboardButton("17:00", callback_data="time_17:00"),
        InlineKeyboardButton("17:30", callback_data="time_17:30"),
        InlineKeyboardButton("18:00", callback_data="time_18:00"),
        InlineKeyboardButton("18:30", callback_data="time_18:30"),
        InlineKeyboardButton("19:00", callback_data="time_19:00"),
        InlineKeyboardButton("19:30", callback_data="time_19:30"),
        InlineKeyboardButton("20:00", callback_data="time_20:00"),
        InlineKeyboardButton("20:30", callback_data="time_20:30"),
        InlineKeyboardButton("21:00", callback_data="time_21:00"),
        InlineKeyboardButton("21:30", callback_data="time_21:30")
    )
    keyboard.add(InlineKeyboardButton("⬅️ Назад к услугам", callback_data="back_to_category"))
    return keyboard

# ---------- КОМАНДА /START ----------
@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_data[message.from_user.id] = {}
    await message.answer(
        "👋 Добро пожаловать в BeautyLoftStudio!\n"
        "Выберите категорию услуг:",
        reply_markup=get_categories_menu()
    )

# ---------- ОБРАБОТКА КАТЕГОРИЙ ----------
@dp.callback_query(lambda c: c.data.startswith('cat_'))
async def process_category(callback_query: types.CallbackQuery):
    category = callback_query.data.replace('cat_', '')
    user_data[callback_query.from_user.id]['category'] = category
    
    menus = {
        'lashes': get_lashes_menu,
        'brows': get_brows_menu,
        'manicure': get_manicure_menu,
        'haircuts': get_haircuts_menu,
        'coloring': get_coloring_menu,
        'complex': get_complex_coloring_menu,
        'care': get_care_menu,
        'courses': get_courses_menu
    }
    
    category_names = {
        'lashes': '👁 Ресницы',
        'brows': '👁 Брови',
        'manicure': '💅 Маникюр',
        'haircuts': '✂️ Стрижки',
        'coloring': '🎨 Окрашивание волос',
        'complex': '💎 Сложное окрашивание',
        'care': '💆 Уход за волосами',
        'courses': '🎓 Курсы'
    }
    
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        f"📋 {category_names.get(category, 'Услуги')}:\nВыберите конкретную услугу:",
        reply_markup=menus.get(category, get_categories_menu)()
    )

# ---------- ОБРАБОТКА ВЫБОРА УСЛУГИ ----------
@dp.callback_query(lambda c: c.data.startswith('service_'))
async def process_service(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    service_code = callback_query.data
    
    # Красивые названия для вывода
    service_names = {
        # Ресницы
        'service_lashes_complex': 'Ламинирование/окрашивание ресниц (комплекс)',
        'service_lashes_lamination': 'Ламинирование ресниц',
        'service_lashes_color': 'Окрашивание ресниц',
        'service_lashes_bottom': 'Ламинирование нижних ресниц',
        'service_lashes_bottom_color': 'Окрашивание нижних ресниц',
        'service_lashes_classic': 'Наращивание Классика',
        'service_lashes_2d': 'Наращивание 2D',
        'service_lashes_3d': 'Наращивание 3D',
        'service_lashes_4d': 'Наращивание 4D+',
        'service_lashes_remove': 'Снятие чужих ресниц',
        'service_lashes_colorful': 'Цветные ресницы',
        'service_lashes_effect': 'Эффекты (изгиб М, L)',
        # Брови
        'service_brows_complex': 'Окрашивание/коррекция бровей (комплекс)',
        'service_brows_color': 'Окрашивание бровей',
        'service_brows_henna': 'Окрашивание бровей (хной)',
        'service_brows_correction': 'Коррекция бровей (воск/пинцет)',
        'service_brows_lami_complex': 'Ламинирование/окрашивание бровей (комплекс)',
        'service_brows_lamination': 'Ламинирование бровей',
        # Маникюр
        'service_manicure_complex': 'Комплекс маникюра с покрытием',
        'service_manicure_gel': 'Комплекс маникюра с гелевым покрытием',
        'service_manicure_hygiene': 'Гигиенический маникюр',
        'service_manicure_male': 'Мужской маникюр',
        'service_manicure_medical': 'Маникюр с лечебным покрытием',
        'service_manicure_extension': 'Наращивание ногтей',
        'service_manicure_repair': 'Ремонт ногтя',
        'service_manicure_design': 'Простой дизайн',
        'service_manicure_french': 'Френч',
        # Стрижки
        'service_haircut_women': 'Женская стрижка',
        'service_haircut_tips': 'Стрижка кончиков',
        'service_haircut_men': 'Мужская стрижка',
        # Окрашивание волос
        'service_color_one': 'Окрашивание в один тон',
        'service_color_gray': 'Окрашивание (седые волосы)',
        'service_color_toning': 'Тонирование волос',
        'service_color_short': 'Окрашивание (короткие)',
        'service_color_long': 'Окрашивание (длинные)',
        'service_color_brushing': 'Мытье + сушка (брашинг)',
        # Сложное окрашивание
        'service_complex_highlight': 'Мелирование/Шатуш',
        'service_complex_balayage': 'Балаяж',
        'service_complex_ombre': 'Омбре/Сомбре',
        'service_complex_colorization': 'Колорирование (2-3 цв)',
        'service_complex_airtouch': 'AirTouch',
        # Уход
        'service_care_hydration': 'Hydration Boost (увлажнение)',
        'service_care_repair': 'Repair Ritual (восстановление)',
        'service_care_scalp': 'Scalp Balance (кожа головы)',
        'service_care_volume': 'Volume Therapy (объем)',
        'service_care_express': 'Express Moroccanoil (экспресс)',
        'service_care_smooth': 'Smooth & Shine (разглаживание)',
        # Курсы
        'service_course_base': 'Базовый курс маникюра',
        'service_course_advanced': 'Повышение квалификации',
        'service_course_combo': 'Комбо (базовый+повышение)',
        'service_course_express': 'Комбо ЭКСПРЕСС'
    }
    
    service_name = service_names.get(service_code, 'Услуга')
    
    await bot.answer_callback_query(callback_query.id)
    
    # Сохраняем в данные пользователя
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['service'] = service_name
    
    await bot.send_message(
        user_id,
        f"✅ Вы выбрали: *{service_name}*\n\n"
        f"Теперь выберите удобное время:",
        parse_mode="Markdown",
        reply_markup=get_time_buttons()
    )

# ---------- ОБРАБОТКА ВРЕМЕНИ ----------
@dp.callback_query(lambda c: c.data.startswith('time_'))
async def process_time(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    time_slot = callback_query.data.replace('time_', '')
    service = user_data.get(user_id, {}).get('service', 'Услуга')
    
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        user_id,
        f"✅ *Запись создана!*\n\n"
        f"📌 Услуга: {service}\n"
        f"⏰ Время: {time_slot}\n\n"
        f"Скоро администратор подтвердит запись.",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardRemove()
    )
    
    # Уведомление администратору
    admin_id = 123456789  # ← ВСТАВЬТЕ ВАШ ID (узнать через @userinfobot)
    await bot.send_message(
        admin_id,
        f"🔔 *НОВАЯ ЗАПИСЬ!*\n"
        f"Клиент: @{callback_query.from_user.username or 'без юзернейма'}\n"
        f"Услуга: {service}\n"
        f"Время: {time_slot}",
        parse_mode="Markdown"
    )

# ---------- КНОПКИ НАЗАД ----------
@dp.callback_query(lambda c: c.data == "back_to_categories")
async def back_to_categories(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        "👋 Выберите категорию услуг:",
        reply_markup=get_categories_menu()
    )

@dp.callback_query(lambda c: c.data == "back_to_category")
async def back_to_category(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    category = user_data.get(user_id, {}).get('category', 'lashes')
    
    menus = {
        'lashes': get_lashes_menu,
        'brows': get_brows_menu,
        'manicure': get_manicure_menu,
        'haircuts': get_haircuts_menu,
        'coloring': get_coloring_menu,
        'complex': get_complex_coloring_menu,
        'care': get_care_menu,
        'courses': get_courses_menu
    }
    
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        "📋 Выберите услугу:",
        reply_markup=menus.get(category, get_categories_menu)()
    )

# ---------- ЗАПУСК БОТА И ВЕБ-СЕРВЕРА ----------
def run_bot():
    asyncio.run(dp.start_polling(bot))

@app.route('/')
def hello():
    return "🤖 BeautyLoftStudio Bot is running!"

@app.route('/health')
def health():
    return "OK"

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
