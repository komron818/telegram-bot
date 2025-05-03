from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import asyncio

API_TOKEN = 'YOUR_API_TOKEN'
ADMIN_ID = 6497374401

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher()

class OrderState(StatesGroup):
    waiting_contact = State()
    waiting_location = State()
    choosing_product = State()
    choosing_quantity = State()

products = {
    "eggs": {"name": "Яйца (30шт)", "price": 40000},
    "water5": {"name": "Вода 5 л", "price": 6000},
    "water10": {"name": "Вода 10 л", "price": 11000},
    "potato": {"name": "Картошка 1 кг", "price": 15000},
    "sugar": {"name": "Сахар 1 кг", "price": 20000},
    "oil": {"name": "Масло 1 л", "price": 25000},
}

user_orders = {}
user_contacts = {}

@dp.message(lambda message: message.text == "/start")
async def start(message: types.Message, state: FSMContext):
    user_orders[message.from_user.id] = {}
    user_contacts[message.from_user.id] = {}
    contact_btn = KeyboardButton(text="📱 Отправить номер", request_contact=True)
    contact_kb = ReplyKeyboardMarkup(keyboard=[[contact_btn]], resize_keyboard=True)
    await message.answer("Сначала отправьте свой номер:", reply_markup=contact_kb)
    await state.set_state(OrderState.waiting_contact)

@dp.message(lambda message: message.contact, OrderState.waiting_contact)
async def receive_contact(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_contacts[user_id]["phone"] = message.contact.phone_number
    location_btn = KeyboardButton(text="📍 Отправить геолокацию", request_location=True)
    location_kb = ReplyKeyboardMarkup(keyboard=[[location_btn]], resize_keyboard=True)
    await message.answer("Теперь отправьте геолокацию:", reply_markup=location_kb)
    await state.set_state(OrderState.waiting_location)

@dp.message(lambda message: message.location, OrderState.waiting_location)
async def receive_location(message: types.Message, state: FSMContext):
    await message.answer("Выберите товар:")
    kb = ReplyKeyboardBuilder()
    for key, item in products.items():
        kb.button(text=item["name"])
    kb.button(text="Корзина")
    await message.answer("Выберите товар:", reply_markup=kb.as_markup(resize_keyboard=True))
    await state.set_state(OrderState.choosing_product)

@dp.message(OrderState.choosing_product)
async def choose_product(message: types.Message, state: FSMContext):
    product_name = message.text
    for key, item in products.items():
        if item["name"] == product_name:
            await state.update_data(selected_product=key)
            kb = ReplyKeyboardBuilder()
            for i in range(1, 11):
                kb.button(text=str(i))
            kb.button(text="Назад")
            await message.answer(f"Сколько штук '{product_name}' вы хотите?", reply_markup=kb.as_markup(resize_keyboard=True))
            await state.set_state(OrderState.choosing_quantity)
            return
    if product_name == "Корзина":
        await show_cart(message)
    else:
        await message.answer("Пожалуйста, выберите товар из списка.")

@dp.message(OrderState.choosing_quantity)
async def choose_quantity(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        return await receive_location(message, state)
    if not message.text.isdigit():
        return await message.answer("Введите количество от 1 до 10.")
    qty = int(message.text)
    if qty < 1 or qty > 10:
        return await message.answer("Введите количество от 1 до 10.")
    data = await state.get_data()
    product_key = data["selected_product"]
    user_id = message.from_user.id
    user_orders[user_id][product_key] = user_orders[user_id].get(product_key, 0) + qty
    await receive_location(message, state)

async def show_cart(message: types.Message):
    user_id = message.from_user.id
    order = user_orders.get(user_id, {})
    if not order:
        await message.answer("Ваша корзина пуста.")
        return
    text = "Ваш чек:

"
    total = 0
    for key, qty in order.items():
        item = products[key]
        price = item["price"] * qty
        total += price
        text += f"{item['name']} — {qty} шт. = {price:,} сум
"
    text += f"
Общая сумма: {total:,} сум"
    confirm_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Подтвердить")], [KeyboardButton(text="Назад")]], resize_keyboard=True)
    await message.answer(text, reply_markup=confirm_kb)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())