
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.enums import ParseMode

API_TOKEN = 'YOUR_API_TOKEN_HERE'
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

class OrderState(StatesGroup):
    choosing_product = State()
    waiting_contact = State()
    waiting_location = State()

user_orders = {}

@dp.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    user_orders[message.from_user.id] = []
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Яйца"), KeyboardButton(text="Картошка")],
            [KeyboardButton(text="Сахар"), KeyboardButton(text="Масло")],
            [KeyboardButton(text="Корзина")]
        ],
        resize_keyboard=True
    )
    await message.answer("Добро пожаловать в бот Oson hayot!
Выберите товар:", reply_markup=kb)
    await state.set_state(OrderState.choosing_product)

@dp.message(F.text == "Корзина")
async def show_cart(message: Message, state: FSMContext):
    orders = user_orders.get(message.from_user.id, [])
    if not orders:
        await message.answer("Ваша корзина пуста.")
        return

    total = 0
    text = "Ваш чек:

"
    for item in orders:
        name = item["name"]
        qty = item["qty"]
        price = item["price"]
        subtotal = qty * price
        total += subtotal
        text += f"{name} — {qty} шт. = {subtotal:,} сум
"

    text += f"
Общая сумма: {total:,} сум"
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Подтвердить"), KeyboardButton(text="Назад")]
        ],
        resize_keyboard=True
    )
    await message.answer(text, reply_markup=kb)
