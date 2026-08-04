import os
import asyncio
import logging
import threading
from datetime import datetime, timedelta
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, BotCommand, BotCommandScopeDefault

# ---------- НАСТРОЙКИ ----------
API_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not API_TOKEN:
    raise ValueError("Переменная TELEGRAM_TOKEN не найдена!")

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

user_data = {}

# ---------- ID АДМИНИСТРАТОРА ----------
ADMIN_ID = 742585100  # ← ID администратора
ADMIN_USERNAME = "beautyloftstudio"  # ← юзернейм администратора

# ---------- НАСТРОЙКА МЕНЮ КОМАНД (появляется справа) ----------
async def set_commands():
    commands = [
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="book", description="📝 Записаться"),
        BotCommand(command="admin", description="💬 Написать администратору"),
        BotCommand(command="cancel", description="❌ Отменить запись")
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    print("✅ Меню команд установлено")

# ---------- СОСТОЯНИЯ FSM ----------
class BookingStates(StatesGroup):
    choosing_category = State()
    choosing_service = State()
    choosing_date = State()
    choosing_time = State()
    entering_phone = State()

# ---------- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ КЛАВИАТУР ----------
def create_keyboard(buttons, row_width=2):
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

# ---------- ГЕНЕРАЦИЯ ДАТ (следующие 14 дней) ----------
def get_dates_keyboard():
    today = datetime.now().date()
    buttons = []
    
    for i in range(14):
        date = today + timedelta(days=i)
        day_names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        day_name = day_names[date.weekday()]
        date_str = date.strftime("%d.%m.%Y")
        display = f"{day_name} {date_str}"
        buttons.append((display, f"date_{date_str}"))
    
    buttons.append(("⬅️ Назад в меню", "back_to_main"))
    return create_keyboard(buttons, row_width=2)

# ---------- МЕНЮ КАТЕГОРИЙ ----------
def get_categories_menu():
    buttons = [
        ("👁 Ресницы", "cat_lashes"),
        ("👁 Брови", "cat_brows"),
        ("💅 Маникюр", "cat_manicure"),
        ("✂️ Стрижки", "cat_haircuts"),
        ("🎨 Окрашивание волос", "cat_coloring"),
        ("💎 Сложное окрашивание", "cat_complex"),
        ("💆 Уход за волосами", "cat_care"),
        ("🎓 Курсы", "cat_courses"),
        ("⬅️ Назад в меню", "back_to_main")
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
        ("⬅️ Назад к категориям", "back_to_categories")
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
        ("⬅️ Назад к категориям", "back_to_categories")
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
        ("⬅️ Назад к категориям", "back_to_categories")
    ]
    return create_keyboard(buttons, row_width=1)

def get_haircuts_menu():
    buttons = [
        ("✂️ Женская стрижка", "service_haircut_women"),
        ("✂️ Стрижка кончиков", "service_haircut_tips"),
        ("✂️ Мужская стрижка", "service_haircut_men"),
        ("⬅️ Назад к категориям", "back_to_categories")
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
        ("⬅️ Назад к категориям", "back_to_categories")
    ]
    return create_keyboard(buttons, row_width=1)

def get_complex_coloring_menu():
    buttons = [
        ("💎 Мелирование/Шатуш", "service_complex_highlight"),
        ("💎 Балаяж", "service_complex_balayage"),
        ("💎 Омбре/Сомбре", "service_complex_ombre"),
        ("💎 Колорирование (2-3 цв)", "service_complex_colorization"),
        ("💎 AirTouch", "service_complex_airtouch"),
        ("⬅️ Назад к категориям", "back_to_categories")
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
        ("⬅️ Назад к категориям", "back_to_categories")
    ]
    return create_keyboard(buttons, row_width=1)

def get_courses_menu():
    buttons = [
        ("📚 Базовый курс маникюра", "service_course_base"),
        ("📚 Повышение квалификации", "service_course_advanced"),
        ("📚 Комбо (базовый+повышение)", "service_course_combo"),
        ("📚 Комбо ЭКСПРЕСС", "service_course_express"),
        ("⬅️ Назад к категориям", "back_to_categories")
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
        ("⬅️ Назад к дате", "back_to_date")
    ]
    return create_keyboard(buttons, row_width=4)

# ---------- КЛАВИАТУРА ДЛЯ НОМЕРА ТЕЛЕФОНА ----------
def get_phone_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

# ---------- КОМАНДА /START ----------
@dp.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    await state.clear()
    user_data[message.from_user.id] = {}
    await message.answer(
        "👋 Добро пожаловать в *BeautyLoftStudio*!\n\n"
        "Используйте кнопки в меню справа 👉\n"
        "или нажмите /book для записи",
        parse_mode="Markdown"
    )

# ---------- КОМАНДА /BOOK (Записаться) ----------
@dp.message(Command("book"))
async def book_command(message: types.Message, state: FSMContext):
    await state.clear()
    user_data[message.from_user.id] = {}
    await message.answer(
        "📋 Выберите категорию услуги:",
        reply_markup=get_categories_menu()
    )
    await state.set_state(BookingStates.choosing_category)

# ---------- КОМАНДА /ADMIN (Написать администратору) ----------
@dp.message(Command("admin"))
async def admin_command(message: types.Message):
    # Создаем глубокую ссылку на администратора
    admin_link = f"https://t.me/{ADMIN_USERNAME}"
    await message.answer(
        f"💬 *Связаться с администратором*\n\n"
        f"Нажмите на кнопку ниже, чтобы открыть чат с администратором:\n"
        f"👉 [Написать @{ADMIN_USERNAME}]({admin_link})\n\n"
        f"Или просто перейдите по ссылке: {admin_link}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💬 Написать администратору",
                        url=admin_link
                    )
                ]
            ]
        )
    )

# ---------- КОМАНДА /CANCEL (Отмена) ----------
@dp.message(Command("cancel"))
async def cancel_command(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("❌ Нет активной записи для отмены.")
        return
    
    await state.clear()
    await message.answer(
        "❌ Запись отменена.\n"
        "Чтобы начать заново, используйте команду /book",
        reply_markup=types.ReplyKeyboardRemove()
    )

# ---------- ОБРАБОТКА КАТЕГОРИЙ ----------
@dp.callback_query(lambda c: c.data.startswith('cat_'))
async def process_category(callback_query: types.CallbackQuery, state: FSMContext):
    category = callback_query.data.replace('cat_', '')
    await state.update_data(category=category)
    
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
    await state.set_state(BookingStates.choosing_service)

# ---------- ОБРАБОТКА ВЫБОРА УСЛУГИ ----------
@dp.callback_query(lambda c: c.data.startswith('service_'))
async def process_service(callback_query: types.CallbackQuery, state: FSMContext):
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
    await state.update_data(service=service_name)
    
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        f"✅ Вы выбрали: *{service_name}*\n\n"
        f"📅 Теперь выберите *дату* записи:",
        parse_mode="Markdown",
        reply_markup=get_dates_keyboard()
    )
    await state.set_state(BookingStates.choosing_date)

# ---------- ОБРАБОТКА ВЫБОРА ДАТЫ ----------
@dp.callback_query(lambda c: c.data.startswith('date_'))
async def process_date(callback_query: types.CallbackQuery, state: FSMContext):
    date_str = callback_query.data.replace('date_', '')
    
    try:
        selected_date = datetime.strptime(date_str, "%d.%m.%Y").date()
        today = datetime.now().date()
        
        if selected_date < today:
            await bot.answer_callback_query(
                callback_query.id,
                text="❌ Эта дата уже прошла! Выберите другую.",
                show_alert=True
            )
            return
    except ValueError:
        await bot.answer_callback_query(callback_query.id, text="❌ Ошибка формата даты")
        return
    
    await state.update_data(date=date_str)
    
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        f"📅 Вы выбрали: *{date_str}*\n\n"
        f"⏰ Теперь выберите *время*:",
        parse_mode="Markdown",
        reply_markup=get_time_buttons()
    )
    await state.set_state(BookingStates.choosing_time)

# ---------- ОБРАБОТКА ВЫБОРА ВРЕМЕНИ ----------
@dp.callback_query(lambda c: c.data.startswith('time_'))
async def process_time(callback_query: types.CallbackQuery, state: FSMContext):
    time_slot = callback_query.data.replace('time_', '')
    await state.update_data(time=time_slot)
    
    data = await state.get_data()
    service = data.get('service', 'Услуга')
    date = data.get('date', 'дата не выбрана')
    
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        f"✅ Вы выбрали:\n"
        f"📌 Услуга: *{service}*\n"
        f"📅 Дата: *{date}*\n"
        f"⏰ Время: *{time_slot}*\n\n"
        f"📱 Теперь отправьте ваш *номер телефона* "
        f"(нажмите кнопку ниже):",
        parse_mode="Markdown",
        reply_markup=get_phone_keyboard()
    )
    await state.set_state(BookingStates.entering_phone)

# ---------- ОБРАБОТКА НОМЕРА ТЕЛЕФОНА ----------
@dp.message(StateFilter(BookingStates.entering_phone))
async def process_phone(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ Запись отменена.\n"
            "Чтобы начать заново, используйте команду /book",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return
    
    if message.contact:
        phone = message.contact.phone_number
    elif message.text and message.text.replace('+', '').replace('-', '').replace(' ', '').isdigit():
        phone = message.text
    else:
        await message.answer(
            "❌ Пожалуйста, отправьте номер телефона через кнопку "
            "или введите его цифрами (например, +79991234567)",
            reply_markup=get_phone_keyboard()
        )
        return
    
    # Получаем все данные
    data = await state.get_data()
    service = data.get('service', 'Услуга')
    date = data.get('date', 'дата не выбрана')
    time_slot = data.get('time', 'время не выбрано')
    
    # Сохраняем в user_data
    user_id = message.from_user.id
    user_data[user_id] = {
        'service': service,
        'date': date,
        'time': time_slot,
        'phone': phone,
        'username': message.from_user.username or 'без юзернейма'
    }
    
    # Отправляем подтверждение клиенту
    await message.answer(
        f"✅ *Запись создана!*\n\n"
        f"📌 Услуга: {service}\n"
        f"📅 Дата: {date}\n"
        f"⏰ Время: {time_slot}\n"
        f"📱 Телефон: {phone}\n\n"
        f"Скоро администратор подтвердит запись.",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardRemove()
    )
    
    # Уведомление администратору
    await bot.send_message(
        ADMIN_ID,
        f"🔔 *НОВАЯ ЗАПИСЬ!*\n\n"
        f"👤 Клиент: @{message.from_user.username or 'без юзернейма'}\n"
        f"📌 Услуга: {service}\n"
        f"📅 Дата: {date}\n"
        f"⏰ Время: {time_slot}\n"
        f"📱 Телефон: {phone}",
        parse_mode="Markdown"
    )
    
    await state.clear()

# ---------- ОБРАБОТКА ОШИБОЧНЫХ ВВОДОВ ----------
@dp.message(StateFilter(BookingStates.entering_phone))
async def process_phone_error(message: types.Message):
    await message.answer(
        "❌ Пожалуйста, используйте кнопку для отправки номера телефона "
        "или введите его в формате +79991234567",
        reply_markup=get_phone_keyboard()
    )

# ---------- КНОПКИ НАЗАД ----------
@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback_query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        "Выберите действие с помощью команд в меню справа 👉",
        reply_markup=types.ReplyKeyboardRemove()
    )

@dp.callback_query(lambda c: c.data == "back_to_categories")
async def back_to_categories(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        "📋 Выберите категорию услуги:",
        reply_markup=get_categories_menu()
    )
    await state.set_state(BookingStates.choosing_category)

@dp.callback_query(lambda c: c.data == "back_to_date")
async def back_to_date(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        "📅 Выберите дату:",
        reply_markup=get_dates_keyboard()
    )
    await state.set_state(BookingStates.choosing_date)

# ---------- ЗАПУСК ----------
def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

async def main():
    print("🚀 Бот запускается...")
    # Устанавливаем меню команд
    await set_commands()
    try:
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        print(f"❌ Ошибка бота: {e}")

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("⏹️ Бот остановлен")
