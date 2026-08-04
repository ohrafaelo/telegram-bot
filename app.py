import os
import asyncio
import logging
import threading
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

# ---------- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ СОЗДАНИЯ КЛАВИАТУР ----------
def create_keyboard(buttons, row_width=2):
    """Создает клавиатуру из списка кнопок"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    row = []
    for i, (text, callback) in enumerate(buttons):
        row.append(InlineKeyboardButton(text=text, callback_data=callback))
        if (i + 1) % row_width == 0:
            keyboard.inline_keyboard.append(row)
            row = []
    if row:
        keyboard.inline_keyboard.append(row)
    return keyboard

# ---------- ГЛАВНОЕ МЕНЮ (КАТЕГОРИИ) ----------
def get_categories_menu():
    buttons = [
        ("👁 Ресницы", "cat_lashes"),
        ("👁 Брови", "cat_brows"),
        ("💅 Маникюр", "cat_manicure"),
        ("✂️ Стрижки", "cat_haircuts"),
        ("🎨 Окрашивание волос", "cat_coloring"),
        ("💎 Сложное окрашивание", "cat_complex"),
        ("💆 Уход за волосами", "cat_care"),
        ("🎓 Курсы", "cat_courses")
    ]
    return create_keyboard(buttons, row_width=2)

# ---------- МЕНЮ УСЛУГ ПО КАТЕГОРИЯМ ----------
def get_lashes_menu():
    buttons = [
        ("🔄 Ламинирование/окрашивание (комплекс)", "service_lashes_complex"),
        ("✨ Ламинирование ресниц", "service_lashes_lamination"),
        ("🎨 Окрашивание ресниц", "service_lashes_color"),
        ("📏 Ламинирование нижних ресниц", "service_lashes_bottom"),
        ("🎨 Окрашивание нижних ресниц", "service_lashes_bottom_color"),
        ("➕ Наращивание Классика", "service_lashes_classic"),
        ("➕ Наращивание 2D", "service_lashes_2d"),
        ("➕ Наращивание 3D", "service_lashes_3d"),
        ("➕ Наращивание 4D+", "service_lashes_4d"),
        ("🔧 Снятие чужих ресниц", "service_lashes_remove"),
        ("🌈 Цветные ресницы", "service_lashes_colorful"),
        ("🌀 Эффекты (изгиб М, L)", "service_lashes_effect"),
        ("⬅️ Назад", "back_to_categories")
    ]
    return create_keyboard(buttons, row_width=1)

def get_brows_menu():
    buttons = [
        ("🔄 Окрашивание/коррекция (комплекс)", "service_brows_complex"),
        ("🎨 Окрашивание бровей", "service_brows_color"),
        ("🌿 Окрашивание бровей (хной)", "service_brows_henna"),
        ("✂️ Коррекция (воск/пинцет)", "service_brows_correction"),
        ("🔄 Ламинирование/окрашивание (комплекс)", "service_brows_lami_complex"),
        ("✨ Ламинирование бровей", "service_brows_lamination"),
        ("⬅️ Назад", "back_to_categories")
    ]
    return create_keyboard(buttons, row_width=1)

def get_manicure_menu():
    buttons = [
        ("💅 Комплекс с покрытием", "service_manicure_complex"),
        ("💅 Комплекс с гелевым покрытием", "service_manicure_gel"),
        ("🧼 Гигиенический маникюр", "service_manicure_hygiene"),
        ("👔 Мужской маникюр", "service_manicure_male"),
        ("💊 С лечебным покрытием", "service_manicure_medical"),
        ("📏 Наращивание ногтей", "service_manicure_extension"),
        ("🔧 Ремонт ногтя", "service_manicure_repair"),
        ("🎨 Простой дизайн", "service_manicure_design"),
        ("🇫🇷 Френч", "service_manicure_french"),
        ("⬅️ Назад", "back_to_categories")
    ]
    return create_keyboard(buttons, row_width=1)

def get_haircuts_menu():
    buttons = [
        ("✂️ Женская стрижка", "service_haircut_women"),
        ("✂️ Стрижка кончиков", "service_haircut_tips"),
        ("✂️ Мужская стрижка", "service_haircut_men"),
        ("⬅️ Назад", "back_to_categories")
    ]
    return create_keyboard(buttons, row_width=1)

def get_coloring_menu():
    buttons = [
        ("🎨 В один тон", "service_color_one"),
        ("🎨 Сложное (седые)", "service_color_gray"),
        ("🎨 Тонирование", "service_color_toning"),
        ("🎨 Короткие волосы", "service_color_short"),
        ("🎨 Длинные волосы", "service_color_long"),
        ("💨 Мытье + сушка (брашинг)", "service_color_brushing"),
        ("⬅️ Назад", "back_to_categories")
    ]
    return create_keyboard(buttons, row_width=1)

def get_complex_coloring_menu():
    buttons = [
        ("💎 Мелирование/Шатуш", "service_complex_highlight"),
        ("💎 Балаяж", "service_complex_balayage"),
        ("💎 Омбре/Сомбре", "service_complex_ombre"),
        ("💎 Колорирование (2-3 цв)", "service_complex_colorization"),
        ("💎 AirTouch", "service_complex_airtouch"),
        ("⬅️ Назад", "back_to_categories")
    ]
    return create_keyboard(buttons, row_width=1)

def get_care_menu():
    buttons = [
        ("💧 Hydration Boost (увлажнение)", "service_care_hydration"),
        ("🔧 Repair Ritual (восстановление)", "service_care_repair"),
        ("⚖️ Scalp Balance (кожа головы)", "service_care_scalp"),
        ("💨 Volume Therapy (объем)", "service_care_volume"),
        ("⚡ Express Moroccanoil (экспресс)", "service_care_express"),
        ("✨ Smooth & Shine (разглаживание)", "service_care_smooth"),
        ("⬅️ Назад", "back_to_categories")
    ]
    return create_keyboard(buttons, row_width=1)

def get_courses_menu():
    buttons = [
        ("📚 Базовый курс маникюра", "service_course_base"),
        ("📚 Повышение квалификации", "service_course_advanced"),
        ("📚 Комбо (базовый+повышение)", "service_course_combo"),
        ("📚 Комбо ЭКСПРЕСС", "service_course_express"),
        ("⬅️ Назад", "back_to_categories")
    ]
    return create_keyboard(buttons, row_width=1)

# ---------- КНОПКИ ВРЕМЕНИ ----------
def get_time_buttons():
    buttons = [
        ("10:00", "time_10:00"),
        ("10:30", "time_10:30"),
        ("11:00", "time_11:00"),
        ("11:30", "time_11:30"),
        ("12:00", "time_12:00"),
        ("12:30", "time_12:30"),
        ("13:00", "time_13:00"),
        ("13:30", "time_13:30"),
        ("14:00", "time_14:00"),
        ("14:30", "time_14:30"),
        ("15:00", "time_15:00"),
        ("15:30", "time_15:30"),
        ("16:00", "time_16:00"),
        ("16:30", "time_16:30"),
        ("17:00", "time_17:00"),
        ("17:30", "time_17:30"),
        ("18:00", "time_18:00"),
        ("18:30", "time_18:30"),
        ("19:00", "time_19:00"),
        ("19:30", "time_19:30"),
        ("20:00", "time_20:00"),
        ("20:30", "time_20:30"),
        ("21:00", "time_21:00"),
        ("21:30", "time_21:30"),
        ("⬅️ Назад к услугам", "back_to_category")
    ]
    return create_keyboard(buttons, row_width=4)

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
    
    service_names = {
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
        'service_brows_complex': 'Окрашивание/коррекция бровей (комплекс)',
        'service_brows_color': 'Окрашивание бровей',
        'service_brows_henna': 'Окрашивание бровей (хной)',
        'service_brows_correction': 'Коррекция бровей (воск/пинцет)',
        'service_brows_lami_complex': 'Ламинирование/окрашивание бровей (комплекс)',
        'service_brows_lamination': 'Ламинирование бровей',
        'service_manicure_complex': 'Комплекс маникюра с покрытием',
        'service_manicure_gel': 'Комплекс маникюра с гелевым покрытием',
        'service_manicure_hygiene': 'Гигиенический маникюр',
        'service_manicure_male': 'Мужской маникюр',
        'service_manicure_medical': 'Маникюр с лечебным покрытием',
        'service_manicure_extension': 'Наращивание ногтей',
        'service_manicure_repair': 'Ремонт ногтя',
        'service_manicure_design': 'Простой дизайн',
        'service_manicure_french': 'Френч',
        'service_haircut_women': 'Женская стрижка',
        'service_haircut_tips': 'Стрижка кончиков',
        'service_haircut_men': 'Мужская стрижка',
        'service_color_one': 'Окрашивание в один тон',
        'service_color_gray': 'Окрашивание (седые волосы)',
        'service_color_toning': 'Тонирование волос',
        'service_color_short': 'Окрашивание (короткие)',
        'service_color_long': 'Окрашивание (длинные)',
        'service_color_brushing': 'Мытье + сушка (брашинг)',
        'service_complex_highlight': 'Мелирование/Шатуш',
        'service_complex_balayage': 'Балаяж',
        'service_complex_ombre': 'Омбре/Сомбре',
        'service_complex_colorization': 'Колорирование (2-3 цв)',
        'service_complex_airtouch': 'AirTouch',
        'service_care_hydration': 'Hydration Boost (увлажнение)',
        'service_care_repair': 'Repair Ritual (восстановление)',
        'service_care_scalp': 'Scalp Balance (кожа головы)',
        'service_care_volume': 'Volume Therapy (объем)',
        'service_care_express': 'Express Moroccanoil (экспресс)',
        'service_care_smooth': 'Smooth & Shine (разглаживание)',
        'service_course_base': 'Базовый курс маникюра',
        'service_course_advanced': 'Повышение квалификации',
        'service_course_combo': 'Комбо (базовый+повышение)',
        'service_course_express': 'Комбо ЭКСПРЕСС'
    }
    
    service_name = service_names.get(service_code, 'Услуга')
    
    await bot.answer_callback_query(callback_query.id)
    
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['service'] = service_name
    
    await bot.send_message(
        user_id,
        f"✅ Вы выбрали: *{service_name}*\n\nТеперь выберите удобное время:",
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
    
    admin_id = 742585100  # ← ВСТАВЬТЕ ВАШ ID
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

# ---------- ЗАПУСК ФЛАСК В ОТДЕЛЬНОМ ПОТОКЕ ----------
def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ---------- ГЛАВНЫЙ ЗАПУСК ----------
async def main():
    print("🚀 Бот запускается...")
    try:
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        print(f"❌ Ошибка бота: {e}")

if __name__ == "__main__":
    # Flask в фоне
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Бот в главном потоке
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("⏹️ Бот остановлен")
