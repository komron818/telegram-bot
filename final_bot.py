
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
    "eggs": {"name": "   (30)", "price": 40000},
    "water5": {"name": " 5 ", "price": 6000},
    "water10": {"name": " 10 ", "price": 11000},
    "potato": {"name": " 1 ", "price": 15000},
    "sugar": {"name": " 1 ", "price": 20000},
    "oil": {"name": " 1 ", "price": 25000}
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

    contact_kb = ReplyKeyboardMarkup(keyboard=[[contact_btn]], resize_keyboard=True, one_time_keyboard=True)


"" Call : +998(98)888-81-10

    await state.set_state(OrderState.waiting_contact)

@dp.message(lambda message: message.contact)
async def receive_contact(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_contacts[user_id]["phone"] = message.contact.phone_number

    location_kb = ReplyKeyboardMarkup(keyboard=[[location_btn]], resize_keyboard=True, one_time_keyboard=True)

    await state.set_state(OrderState.waiting_location)

@dp.message(lambda message: message.location)
async def receive_location(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_contacts[user_id]["location"] = f"{message.location.latitude},{message.location.longitude}"

    #  
    contact = user_contacts[user_id].get("phone", "")
    location = user_contacts[user_id].get("location", "")
    await bot.send_message(
        ADMIN_ID,
        f"  :
ID: {user_id}"
    )

    #  
    
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
    builder.inline_keyboard = rows
    await message.answer(" :", reply_markup=builder.as_markup())
)
    await state.set_state(OrderState.choosing)

#       ...
