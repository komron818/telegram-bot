
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio

TOKEN = "8197970222:AAGotKTpT8t9ZSli6VbJKhPxNAWTKI2q7j8"
ADMIN_ID = 6497374401

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

products = {
    "eggs": {"name": "Яйца на флейке (30шт)", "price": 40000},
    "water5": {"name": "Вода 5 литров", "price": 6000},
    "water10": {"name": "Вода 10 литров", "price": 11000},
    "potato": {"name": "Картошка 1 кг", "price": 15000},
    "sugar": {"name": "Сахар 1 кг", "price": 20000},
    "oil": {"name": "Масло 1 литр", "price": 25000}
}

class OrderState(StatesGroup):
    waiting_contact = State()
    waiting_location = State()
    choosing = State()
    quantity = State()
    cart = State()

user_orders = {}
user_contacts = {}

@dp.message(lambda message: message.text == "/start")
async def start(message: Message, state: FSMContext):
    user_orders[message.from_user.id] = {}
    user_contacts[message.from_user.id] = {}

    contact_btn = KeyboardButton(text="📱 Отправить номер", request_contact=True)
    contact_kb = ReplyKeyboardMarkup(keyboard=[[contact_btn]], resize_keyboard=True, one_time_keyboard=True)

    welcome = ("🥳 Вас приветствует бот <b>Oson hayot</b>!

""🚚 Бесплатная доставка нужных веществ до вашего дома
""📶 Качество вещей на вышем уровне
""⏰ Доставка с 10:00 до 23:00
""☎️ Call центр: +998(98)888-81-10
""⌛️ Доставка в течение часа

""🟦 Сначала отправьте свой номер:")
    await state.set_state(OrderState.waiting_contact)

@dp.message(lambda message: message.contact)
async def receive_contact(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_contacts[user_id]["phone"] = message.contact.phone_number

    location_btn = KeyboardButton(text="📍 Отправить геолокацию", request_location=True)
    location_kb = ReplyKeyboardMarkup(keyboard=[[location_btn]], resize_keyboard=True, one_time_keyboard=True)

    await message.answer("Теперь отправьте вашу геолокацию:", reply_markup=location_kb)
    await state.set_state(OrderState.waiting_location)

@dp.message(lambda message: message.location)
async def receive_location(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_contacts[user_id]["location"] = f"{message.location.latitude},{message.location.longitude}"

    # Уведомим админа
    contact = user_contacts[user_id].get("phone", "нет")
    location = user_contacts[user_id].get("location", "нет")
    await bot.send_message(
        ADMIN_ID,
        f"🆕 Новый пользователь:
📞 {contact}
📍 {location}
ID: {user_id}"
    )

    # Показываем товары
    
    builder = InlineKeyboardBuilder()
    rows = []
    row = []
    for idx, (key, item) in enumerate(products.items()):
        row.append(types.InlineKeyboardButton(text=item["name"], callback_data=f"product:{key}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([types.InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")])
    builder.inline_keyboard = rows
    await message.answer("Выберите товар:", reply_markup=builder.as_markup())
)
    await state.set_state(OrderState.choosing)

# Остальной код обработки товаров остаётся как был...
