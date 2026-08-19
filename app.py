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

# ---------- ХРАНИЛИЩЕ ЗАБЛОКИРОВАННЫХ СЛОТОВ ----------
# Структура: { "10.08.2026": ["10:00", "12:30", "15:00"] }
# Если дата есть в словаре и список пустой [] — вся дата заблокирована
blocked_slots = {}

# ---------- НАСТРОЙКА МЕНЮ КОМАНД ----------
async def set_commands():
    commands = [
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="book", description="📝 Записаться"),
        BotCommand(command="admin", description="💬 Написать администратору"),
        BotCommand(command="admin_panel", description="⚙️ Админ-панель")
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    print("✅ Меню команд установлено")

# ---------- СОСТОЯНИЯ FSM ----------
class BookingStates(StatesGroup):
    choosing_category = State()
    choosing_service = State()
    choosing_date = State()
    choosing_time = State()
    entering_name = State()
    entering_phone = State()

class AdminStates(StatesGroup):
    choosing_action = State()
    choosing_block_date = State()
    choosing_block_time = State()
    choosing_unblock_date = State()
    choosing_unblock_time = State()

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
def get_dates_keyboard(admin_mode=False):
    today = datetime.now().date()
    buttons = []
    
    for i in range(14):
        date = today + timedelta(days=i)
        day_names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        day_name = day_names[date.weekday()]
        date_str = date.strftime("%d.%m.%Y")
        
        # Проверяем, заблокирована ли дата полностью
        is_blocked = date_str in blocked_slots and len(blocked_slots[date_str]) == 0
        
        # Добавляем эмодзи для заблокированных дат
        if is_blocked:
            display = f"🔒 {day_name} {date_str}"
        else:
            display = f"{day_name} {date_str}"
            
        buttons.append((display, f"date_{date_str}"))
    
    buttons.append(("⬅️ Назад в меню", "back_to_main"))
    return create_keyboard(buttons, row_width=2)

# ---------- МЕНЮ КАТЕГОРИЙ ----------
def get_categories_menu():
    buttons = [
        ("👁 Ресницы", "cat_lashes"),
        ("😉 Брови", "cat_brows"),
        ("💅 Маникюр", "cat_manicure"),
        ("💇 Стрижки", "cat_haircuts"),
        ("🧑‍🎨 Окрашивание волос", "cat_coloring"),
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
        ("✨ Ламинирование нижних ресниц", "service_lashes_bottom"),
        ("🎨 Окрашивание нижних ресниц", "service_lashes_bottom_color"),
        ("➕ Наращивание Классика", "service_lashes_classic"),
        ("➕ Наращивание 2D", "service_lashes_2d"),
        ("➕ Наращивание 3D", "service_lashes_3d"),
        ("➕ Наращивание 4D+", "service_lashes_4d"),
        ("🪄 Снятие чужих ресниц", "service_lashes_remove"),
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
        ("🪄 Коррекция (воск/пинцет)", "service_brows_correction"),
        ("🔄 Ламинирование/окрашивание (комплекс)", "service_brows_lami_complex"),
        ("✨ Ламинирование бровей", "service_brows_lamination"),
        ("⬅️ Назад к категориям", "back_to_categories")
    ]
    return create_keyboard(buttons, row_width=1)

def get_manicure_menu():
    buttons = [
        ("💅 Комплекс с покрытием гель-лак", "service_manicure_complex"),
        ("💅 Комплекс с гелевым покрытием", "service_manicure_gel"),
        ("🧼 Гигиенический маникюр", "service_manicure_hygiene"),
        ("👔 Мужской маникюр", "service_manicure_male"),
        ("💊 С лечебным покрытием", "service_manicure_medical"),
        ("📏 Наращивание ногтей", "service_manicure_extension"),
        ("🔧 Ремонт ногтя", "service_manicure_repair"),
        ("🎨 Простой дизайн", "service_manicure_design"),
        ("🪄 Снятие покрытия", "service_manicure_delete"),
        ("🇫🇷 Френч", "service_manicure_french"),
        ("⬅️ Назад к категориям", "back_to_categories")
    ]
    return create_keyboard(buttons, row_width=1)

def get_haircuts_menu():
    buttons = [
        ("💇‍♀️ Женская стрижка", "service_haircut_women"),
        ("💇 Стрижка кончиков", "service_haircut_tips"),
        ("💇‍♂️ Мужская стрижка", "service_haircut_men"),
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
        ("💨 Мытье + сушка", "service_color_brushing"),
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
def get_time_buttons(date_str=None, admin_mode=False):
    buttons = []
    all_times = [
        "10:00", "10:30", "11:00", "11:30",
        "12:00", "12:30", "13:00", "13:30",
        "14:00", "14:30", "15:00", "15:30",
        "16:00", "16:30", "17:00", "17:30",
        "18:00", "18:30", "19:00", "19:30",
        "20:00", "20:30", "21:00", "21:30"
    ]
    
    # Получаем заблокированные времена для этой даты
    blocked_times = []
    if date_str and date_str in blocked_slots:
        blocked_times = blocked_slots[date_str]
    
    for time in all_times:
        # Проверяем, заблокирован ли этот слот
        is_blocked = time in blocked_times
        display = f"🔒 {time}" if is_blocked and not admin_mode else time
        if admin_mode:
            # В админ-режиме показываем статус
            status = "🔒" if is_blocked else "✅"
            display = f"{status} {time}"
        buttons.append((display, f"time_{time}"))
    
    buttons.append(("⬅️ Назад к дате", "back_to_date"))
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

# ---------- АДМИН-КЛАВИАТУРЫ ----------
def get_admin_main_menu():
    buttons = [
        ("🔒 Заблокировать дату", "admin_block_date"),
        ("🔓 Разблокировать дату", "admin_unblock_date"),
        ("⏰ Заблокировать время", "admin_block_time"),
        ("⏰ Разблокировать время", "admin_unblock_time"),
        ("📋 Показать блокировки", "admin_show_blocks"),
        ("🗑️ Очистить все блокировки", "admin_clear_all"),
        ("⬅️ Назад в меню", "back_to_main")
    ]
    return create_keyboard(buttons, row_width=2)

# ---------- КОМАНДА /START ----------
@dp.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    await state.clear()
    user_data[message.from_user.id] = {}
    await message.answer(
        "👋 Добро пожаловать в *BeautyLoftStudio*!\n\n"
        "Используйте кнопки в меню ✨\n"
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

# ---------- КОМАНДА /ADMIN_PANEL ----------
@dp.message(Command("admin_panel"))
async def admin_panel_command(message: types.Message, state: FSMContext):
    # Проверяем, что это администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет доступа к этой команде.")
        return
    
    await state.clear()
    await message.answer(
        "⚙️ *Админ-панель*\n\n"
        "Выберите действие:",
        parse_mode="Markdown",
        reply_markup=get_admin_main_menu()
    )
    await state.set_state(AdminStates.choosing_action)

# ---------- АДМИН: БЛОКИРОВКА ДАТЫ ----------
@dp.callback_query(lambda c: c.data == "admin_block_date")
async def admin_block_date(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != ADMIN_ID:
        await bot.answer_callback_query(callback_query.id, text="❌ Нет доступа")
        return
    
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        "📅 Выберите дату для блокировки (вся дата будет недоступна):",
        reply_markup=get_dates_keyboard(admin_mode=True)
    )
    await state.set_state(AdminStates.choosing_block_date)

@dp.callback_query(lambda c: c.data.startswith('date_') and c.data not in ['back_to_main', 'back_to_categories', 'back_to_date'])
async def admin_process_block_date(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != ADMIN_ID:
        await bot.answer_callback_query(callback_query.id, text="❌ Нет доступа")
        return
    
    date_str = callback_query.data.replace('date_', '')
    current_state = await state.get_state()
    
    # Проверяем, это админ-блокировка или обычный выбор
    if current_state == AdminStates.choosing_block_date:
        # Блокируем всю дату (пустой список = вся дата заблокирована)
        blocked_slots[date_str] = []
        await bot.answer_callback_query(callback_query.id, text=f"✅ Дата {date_str} заблокирована!")
        await bot.send_message(
            callback_query.from_user.id,
            f"✅ *Дата {date_str} полностью заблокирована!*\n\n"
            f"Клиенты не смогут выбрать эту дату.",
            parse_mode="Markdown",
            reply_markup=get_admin_main_menu()
        )
        await state.set_state(AdminStates.choosing_action)
    else:
        # Обычный выбор даты для клиента
        await process_date(callback_query, state)

# ---------- АДМИН: РАЗБЛОКИРОВКА ДАТЫ ----------
@dp.callback_query(lambda c: c.data == "admin_unblock_date")
async def admin_unblock_date(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != ADMIN_ID:
        await bot.answer_callback_query(callback_query.id, text="❌ Нет доступа")
        return
    
    await bot.answer_callback_query(callback_query.id)
    
    # Показываем только заблокированные даты
    if not blocked_slots:
        await bot.send_message(
            callback_query.from_user.id,
            "ℹ️ Нет заблокированных дат.",
            reply_markup=get_admin_main_menu()
        )
        await state.set_state(AdminStates.choosing_action)
        return
    
    buttons = []
    for date_str in blocked_slots.keys():
        buttons.append((f"🔓 {date_str}", f"unblock_{date_str}"))
    buttons.append(("⬅️ Назад", "admin_back_to_panel"))
    
    keyboard = create_keyboard(buttons, row_width=2)
    await bot.send_message(
        callback_query.from_user.id,
        "📅 Выберите дату для разблокировки:",
        reply_markup=keyboard
    )
    await state.set_state(AdminStates.choosing_unblock_date)

@dp.callback_query(lambda c: c.data.startswith('unblock_'))
async def admin_process_unblock_date(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != ADMIN_ID:
        await bot.answer_callback_query(callback_query.id, text="❌ Нет доступа")
        return
    
    date_str = callback_query.data.replace('unblock_', '')
    
    if date_str in blocked_slots:
        del blocked_slots[date_str]
        await bot.answer_callback_query(callback_query.id, text=f"✅ Дата {date_str} разблокирована!")
        await bot.send_message(
            callback_query.from_user.id,
            f"✅ *Дата {date_str} разблокирована!*",
            parse_mode="Markdown",
            reply_markup=get_admin_main_menu()
        )
    else:
        await bot.answer_callback_query(callback_query.id, text="❌ Дата не найдена")
        await bot.send_message(
            callback_query.from_user.id,
            "ℹ️ Дата не найдена в списке блокировок.",
            reply_markup=get_admin_main_menu()
        )
    
    await state.set_state(AdminStates.choosing_action)

# ---------- АДМИН: БЛОКИРОВКА ВРЕМЕНИ ----------
@dp.callback_query(lambda c: c.data == "admin_block_time")
async def admin_block_time(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != ADMIN_ID:
        await bot.answer_callback_query(callback_query.id, text="❌ Нет доступа")
        return
    
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        "📅 Сначала выберите *дату*, для которой хотите заблокировать время:",
        parse_mode="Markdown",
        reply_markup=get_dates_keyboard(admin_mode=True)
    )
    await state.set_state(AdminStates.choosing_block_time)

@dp.callback_query(lambda c: c.data.startswith('date_') and c.data not in ['back_to_main', 'back_to_categories', 'back_to_date'])
async def admin_process_block_time_date(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != ADMIN_ID:
        await bot.answer_callback_query(callback_query.id, text="❌ Нет доступа")
        return
    
    date_str = callback_query.data.replace('date_', '')
    current_state = await state.get_state()
    
    if current_state == AdminStates.choosing_block_time:
        # Сохраняем дату и показываем времена
        await state.update_data(admin_date=date_str)
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(
            callback_query.from_user.id,
            f"📅 Вы выбрали: *{date_str}*\n\n"
            "⏰ Теперь выберите *время*, которое хотите заблокировать:\n"
            "(🔒 - уже заблокировано)",
            parse_mode="Markdown",
            reply_markup=get_time_buttons(date_str, admin_mode=True)
        )
    else:
        # Обычный выбор даты для клиента
        await process_date(callback_query, state)

@dp.callback_query(lambda c: c.data.startswith('time_') and c.data not in ['back_to_date', 'back_to_main', 'back_to_categories'])
async def admin_process_block_time(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != ADMIN_ID:
        await bot.answer_callback_query(callback_query.id, text="❌ Нет доступа")
        return
    
    time_slot = callback_query.data.replace('time_', '')
    data = await state.get_data()
    date_str = data.get('admin_date')
    
    if not date_str:
        await bot.answer_callback_query(callback_query.id, text="❌ Ошибка: дата не выбрана")
        return
    
    # Инициализируем список для даты, если его нет
    if date_str not in blocked_slots:
        blocked_slots[date_str] = []
    
    # Если время уже заблокировано - разблокируем (переключатель)
    if time_slot in blocked_slots[date_str]:
        blocked_slots[date_str].remove(time_slot)
        action = "разблокировано"
    else:
        blocked_slots[date_str].append(time_slot)
        action = "заблокировано"
    
    await bot.answer_callback_query(callback_query.id, text=f"✅ {time_slot} {action}!")
    await bot.send_message(
        callback_query.from_user.id,
        f"✅ *{time_slot} {action}* для даты {date_str}!\n\n"
        f"Выберите следующее время или вернитесь в меню:",
        parse_mode="Markdown",
        reply_markup=get_time_buttons(date_str, admin_mode=True)
    )

# ---------- АДМИН: РАЗБЛОКИРОВКА ВРЕМЕНИ ----------
@dp.callback_query(lambda c: c.data == "admin_unblock_time")
async def admin_unblock_time(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != ADMIN_ID:
        await bot.answer_callback_query(callback_query.id, text="❌ Нет доступа")
        return
    
    await bot.answer_callback_query(callback_query.id)
    
    # Показываем даты, у которых есть заблокированные времена
    dates_with_times = {d: times for d, times in blocked_slots.items() if times}
    
    if not dates_with_times:
        await bot.send_message(
            callback_query.from_user.id,
            "ℹ️ Нет заблокированных временных слотов.",
            reply_markup=get_admin_main_menu()
        )
        await state.set_state(AdminStates.choosing_action)
        return
    
    buttons = []
    for date_str, times in dates_with_times.items():
        count = len(times)
        buttons.append((f"📅 {date_str} ({count} слотов)", f"unblock_time_{date_str}"))
    buttons.append(("⬅️ Назад", "admin_back_to_panel"))
    
    keyboard = create_keyboard(buttons, row_width=2)
    await bot.send_message(
        callback_query.from_user.id,
        "📅 Выберите дату, для которой хотите разблокировать время:",
        reply_markup=keyboard
    )
    await state.set_state(AdminStates.choosing_unblock_time)

@dp.callback_query(lambda c: c.data.startswith('unblock_time_'))
async def admin_process_unblock_time(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != ADMIN_ID:
        await bot.answer_callback_query(callback_query.id, text="❌ Нет доступа")
        return
    
    date_str = callback_query.data.replace('unblock_time_', '')
    await state.update_data(admin_date=date_str)
    
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        f"📅 Вы выбрали: *{date_str}*\n\n"
        "⏰ Выберите время для разблокировки:\n"
        "(🔒 - заблокировано)",
        parse_mode="Markdown",
        reply_markup=get_time_buttons(date_str, admin_mode=True)
    )

# ---------- АДМИН: ПОКАЗАТЬ БЛОКИРОВКИ ----------
@dp.callback_query(lambda c: c.data == "admin_show_blocks")
async def admin_show_blocks(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != ADMIN_ID:
        await bot.answer_callback_query(callback_query.id, text="❌ Нет доступа")
        return
    
    await bot.answer_callback_query(callback_query.id)
    
    if not blocked_slots:
        await bot.send_message(
            callback_query.from_user.id,
            "ℹ️ *Нет активных блокировок*",
            parse_mode="Markdown",
            reply_markup=get_admin_main_menu()
        )
        await state.set_state(AdminStates.choosing_action)
        return
    
    message = "📋 *Текущие блокировки:*\n\n"
    for date_str, times in blocked_slots.items():
        if not times:
            message += f"🔒 *{date_str}* — ВСЯ ДАТА ЗАБЛОКИРОВАНА\n"
        else:
            times_str = ", ".join(times)
            message += f"📅 *{date_str}* — заблокировано: {times_str}\n"
    
    await bot.send_message(
        callback_query.from_user.id,
        message,
        parse_mode="Markdown",
        reply_markup=get_admin_main_menu()
    )
    await state.set_state(AdminStates.choosing_action)

# ---------- АДМИН: ОЧИСТИТЬ ВСЕ БЛОКИРОВКИ ----------
@dp.callback_query(lambda c: c.data == "admin_clear_all")
async def admin_clear_all(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != ADMIN_ID:
        await bot.answer_callback_query(callback_query.id, text="❌ Нет доступа")
        return
    
    await bot.answer_callback_query(callback_query.id)
    
    # Подтверждение
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, очистить всё", callback_data="admin_clear_confirm"),
            InlineKeyboardButton(text="❌ Нет, отмена", callback_data="admin_clear_cancel")
        ]
    ])
    
    await bot.send_message(
        callback_query.from_user.id,
        "⚠️ *Вы уверены, что хотите очистить все блокировки?*\n\n"
        "Это действие нельзя отменить!",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data == "admin_clear_confirm")
async def admin_clear_confirm(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != ADMIN_ID:
        await bot.answer_callback_query(callback_query.id, text="❌ Нет доступа")
        return
    
    blocked_slots.clear()
    await bot.answer_callback_query(callback_query.id, text="✅ Все блокировки очищены!")
    await bot.send_message(
        callback_query.from_user.id,
        "✅ *Все блокировки успешно очищены!*",
        parse_mode="Markdown",
        reply_markup=get_admin_main_menu()
    )
    await state.set_state(AdminStates.choosing_action)

@dp.callback_query(lambda c: c.data == "admin_clear_cancel")
async def admin_clear_cancel(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != ADMIN_ID:
        await bot.answer_callback_query(callback_query.id, text="❌ Нет доступа")
        return
    
    await bot.answer_callback_query(callback_query.id, text="✅ Отменено")
    await bot.send_message(
        callback_query.from_user.id,
        "✅ Очистка блокировок отменена.",
        reply_markup=get_admin_main_menu()
    )
    await state.set_state(AdminStates.choosing_action)

# ---------- АДМИН: НАЗАД В ПАНЕЛЬ ----------
@dp.callback_query(lambda c: c.data == "admin_back_to_panel")
async def admin_back_to_panel(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != ADMIN_ID:
        await bot.answer_callback_query(callback_query.id, text="❌ Нет доступа")
        return
    
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        "⚙️ *Админ-панель*\n\n"
        "Выберите действие:",
        parse_mode="Markdown",
        reply_markup=get_admin_main_menu()
    )
    await state.set_state(AdminStates.choosing_action)

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
        'brows': '😉 Брови',
        'manicure': '💅 Маникюр',
        'haircuts': '💇 Стрижки',
        'coloring': '🧑‍🎨 Окрашивание волос',
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
        'service_lashes_effect': 'Эффекты (изги
