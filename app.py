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

# ---------- ГЕНЕРАЦИЯ ДАТ ----------
def get_dates_keyboard(admin_mode=False):
    today = datetime.now().date()
    buttons = []
    
    for i in range(14):
        date = today + timedelta(days=i)
        day_names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        day_name = day_names[date.weekday()]
        date_str = date.strftime("%d.%m.%Y")
        
        is_blocked = date_str in blocked_slots and len(blocked_slots[date_str]) == 0
        
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
    
    blocked_times = []
    if date_str and date_str in blocked_slots:
        blocked_times = blocked_slots[date_str]
    
    for time in all_times:
        is_blocked = time in blocked_times
        if admin_mode:
            status = "🔒" if is_blocked else "✅"
            display = f"{status} {time}"
        else:
            display = f"🔒 {time}" if is_blocked else time
        buttons.append((display, f"time_{time}"))
    
    buttons.append(("⬅️ Назад к дате", "back_to_date"))
    return create_keyboard(buttons, row_width=4)

# ---------- КЛАВИАТУРА ДЛЯ ТЕЛЕФОНА ----------
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

# ---------- КОМАНДА /BOOK ----------
@dp.message(Command("book"))
async def book_command(message: types.Message, state: FSMContext):
    await state.clear()
    user_data[message.from_user.id] = {}
    await message.answer(
        "📋 Выберите категорию услуги:",
        reply_markup=get_categories_menu()
    )
    await state.set_state(BookingStates.choosing_category)

# ---------- КОМАНДА /ADMIN ----------
@dp.message(Command("admin"))
async def admin_command(message: types.Message):
    admin_link = f"https://t.me/{ADMIN_USERNAME}"
    await message.answer(
        f"💬 *Связаться с администратором*\n\n"
        f"Нажмите на кнопку ниже, чтобы открыть чат с администратором:\n"
        f"👉 [Написать @{ADMIN_USERNAME}]({admin_link})",
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
    
    if current_state == AdminStates.choosing_block_date:
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
        await process_date(callback_query, state)

# ---------- АДМИН: РАЗБЛОКИРОВКА ДАТЫ ----------
@dp.callback_query(lambda c: c.data == "admin_unblock_date")
async def admin_unblock_date(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != ADMIN_ID:
        await bot.answer_callback_query(callback_query.id, text="❌ Нет доступа")
        return
    
    await bot.answer_callback_query(callback_query.id)
    
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
    
    await bot.send_message(
        callback_query.from_user.id,
        "📅 Выберите дату для разблокировки:",
        reply_markup=create_keyboard(buttons, row_width=2)
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

# ---------- АДМИН: БЛОКИРОВКА ВРЕМЕНИ (исправленная версия) ----------
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
        # СОХРАНЯЕМ ДАТУ В СОСТОЯНИЕ
        await state.update_data(admin_date=date_str)
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(
            callback_query.from_user.id,
            f"📅 Вы выбрали: *{date_str}*\n\n"
            "⏰ Теперь выберите *время*, которое хотите заблокировать:\n"
            "(🔒 - уже заблокировано, ✅ - свободно)",
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
    
    # ПОЛУЧАЕМ ДАТУ ИЗ СОСТОЯНИЯ
    data = await state.get_data()
    date_str = data.get('admin_date')
    
    if not date_str:
        await bot.answer_callback_query(callback_query.id, text="❌ Ошибка: дата не выбрана")
        await bot.send_message(
            callback_query.from_user.id,
            "⚠️ Произошла ошибка. Попробуйте снова:\n"
            "/admin_panel → Заблокировать время",
            reply_markup=get_admin_main_menu()
        )
        await state.set_state(AdminStates.choosing_action)
        return
    
    if date_str not in blocked_slots:
        blocked_slots[date_str] = []
    
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
    
    await bot.send_message(
        callback_query.from_user.id,
        "📅 Выберите дату, для которой хотите разблокировать время:",
        reply_markup=create_keyboard(buttons, row_width=2)
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
        'service_lashes_effect': 'Эффекты (изгиб М, L)',
        'service_brows_complex': 'Окрашивание/коррекция бровей (комплекс)',
        'service_brows_color': 'Окрашивание бровей',
        'service_brows_henna': 'Окрашивание бровей (хной)',
        'service_brows_correction': 'Коррекция бровей (воск/пинцет)',
        'service_brows_lami_complex': 'Ламинирование/окрашивание бровей (комплекс)',
        'service_brows_lamination': 'Ламинирование бровей',
        'service_manicure_complex': 'Комплекс маникюра с покрытием гель-лак',
        'service_manicure_delete': 'Снятие покрытия',
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
        'service_color_brushing': 'Мытье + сушка',
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
    
    # Проверяем, заблокирована ли дата полностью
    if date_str in blocked_slots and len(blocked_slots[date_str]) == 0:
        await bot.answer_callback_query(
            callback_query.id,
            text="❌ Эта дата недоступна для записи!",
            show_alert=True
        )
        return
    
    try:
        selected_date = datetime.strptime(date_str, "%d.%m.%Y").date()
        today = datetime.now().date()
        
        if selected_date < today:
            await bot.answer_callback_query(
                callback_query.id,
                text="❌ Эта дата уже прошла!",
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
        reply_markup=get_time_buttons(date_str)
    )
    await state.set_state(BookingStates.choosing_time)

# ---------- ОБРАБОТКА ВЫБОРА ВРЕМЕНИ ----------
@dp.callback_query(lambda c: c.data.startswith('time_'))
async def process_time(callback_query: types.CallbackQuery, state: FSMContext):
    time_slot = callback_query.data.replace('time_', '')
    data = await state.get_data()
    date_str = data.get('date', '')
    
    # Проверяем, заблокирован ли этот слот
    if date_str in blocked_slots and time_slot in blocked_slots[date_str]:
        await bot.answer_callback_query(
            callback_query.id,
            text="❌ Это время уже заблокировано! Выберите другое.",
            show_alert=True
        )
        return
    
    await state.update_data(time=time_slot)
    
    service = data.get('service', 'Услуга')
    date = data.get('date', 'дата не выбрана')
    
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        f"✅ Вы выбрали:\n"
        f"📌 Услуга: *{service}*\n"
        f"📅 Дата: *{date}*\n"
        f"⏰ Время: *{time_slot}*\n\n"
        f"✏️ Теперь напишите *имя клиента*:",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(BookingStates.entering_name)

# ---------- ОБРАБОТКА ИМЕНИ ----------
@dp.message(StateFilter(BookingStates.entering_name))
async def process_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    
    if len(name) < 2:
        await message.answer(
            "❌ Имя должно содержать хотя бы 2 буквы.\n"
            "Пожалуйста, введите имя клиента:"
        )
        return
    
    await state.update_data(name=name)
    
    await message.answer(
        f"✅ Спасибо, *{name}*!\n\n"
        f"📱 Теперь отправьте *номер телефона*\n"
        f"(нажмите кнопку ниже или введите вручную):",
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
    name = data.get('name', 'не указано')
    
    # Сохраняем в user_data
    user_id = message.from_user.id
    user_data[user_id] = {
        'service': service,
        'date': date,
        'time': time_slot,
        'name': name,
        'phone': phone,
        'username': message.from_user.username or 'без юзернейма'
    }
    
    # Отправляем подтверждение клиенту
    await message.answer(
        f"✅ *Запись создана!*\n\n"
        f"👤 Имя: {name}\n"
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
        f"👤 Имя: {name}\n"
        f"📌 Услуга: {service}\n"
        f"📅 Дата: {date}\n"
        f"⏰ Время: {time_slot}\n"
        f"📱 Телефон: {phone}\n"
        f"👤 Телеграм: @{message.from_user.username or 'без юзернейма'}",
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
        "👋 Добро пожаловать в *BeautyLoftStudio*!\n\n"
        "Используйте кнопки в меню ✨\n"
        "или нажмите /book для записи",
        parse_mode="Markdown"
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
    await state.set_state(BookingStates.choosing_time)

# ---------- ЗАПУСК ----------
def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

async def main():
    print("🚀 Бот запускается...")
    await set_commands()
    try:
        await dp.start_polling(bot, skip_updates=True, handle_signals=False)
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
