
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder
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
    checkout = State()

user_orders = {}
user_contacts = {}

@dp.message(lambda message: message.text == "/start")
async def start(message: Message, state: FSMContext):
    user_orders[message.from_user.id] = {}
    user_contacts[message.from_user.id] = {}

    contact_btn = KeyboardButton(text="Отправить номер", request_contact=True)
    contact_kb = ReplyKeyboardMarkup(keyboard=[[contact_btn]], resize_keyboard=True, one_time_keyboard=True)
    await message.answer("Пожалуйста, отправьте ваш номер телефона:", reply_markup=contact_kb)
    await state.set_state(OrderState.waiting_contact)

@dp.message(lambda message: message.contact)
async def receive_contact(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_contacts[user_id]["phone"] = message.contact.phone_number

    location_btn = KeyboardButton(text="Отправить геолокацию", request_location=True)
    location_kb = ReplyKeyboardMarkup(keyboard=[[location_btn]], resize_keyboard=True, one_time_keyboard=True)

    await message.answer("Теперь отправьте вашу геолокацию:", reply_markup=location_kb)
    await state.set_state(OrderState.waiting_location)

@dp.message(lambda message: message.location)
async def receive_location(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_contacts[user_id]["location"] = f"{message.location.latitude},{message.location.longitude}"

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
    rows.append([types.InlineKeyboardButton(text="Корзина", callback_data="cart")])
    builder.inline_keyboard = rows

    await message.answer("Выберите товар:", reply_markup=builder.as_markup())
    await state.set_state(OrderState.choosing)

@dp.callback_query(lambda c: c.data.startswith("product:"))
async def choose_product(callback: CallbackQuery, state: FSMContext):
    product_key = callback.data.split(":")[1]
    await state.update_data(product_key=product_key)

    kb = InlineKeyboardBuilder()
    for i in range(1, 11):
        kb.button(text=str(i), callback_data=f"qty:{i}")
    kb.adjust(5)
    await callback.message.answer(f"Сколько штук '{products[product_key]['name']}' вы хотите?", reply_markup=kb.as_markup())
    await state.set_state(OrderState.quantity)

@dp.callback_query(lambda c: c.data.startswith("qty:"))
async def select_quantity(callback: CallbackQuery, state: FSMContext):
    qty = int(callback.data.split(":")[1])
    data = await state.get_data()
    product_key = data["product_key"]
    user_id = callback.from_user.id
    user_orders[user_id][product_key] = qty

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
    rows.append([types.InlineKeyboardButton(text="Корзина", callback_data="cart")])
    builder.inline_keyboard = rows

    await callback.message.answer(f"Добавлено: {products[product_key]['name']} - {qty} шт.")
    await callback.message.answer("Выберите следующий товар:", reply_markup=builder.as_markup())
    await state.set_state(OrderState.choosing)

@dp.callback_query(lambda c: c.data == "cart")
async def show_cart(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    order = user_orders.get(user_id, {})
    text = f"""Ваш чек:

"""
    text += f"{item['name']} — {qty} шт. = {price:,} сум
"
    text += f"
Общая сумма: {total:,} сум"

    kb = InlineKeyboardBuilder()
    kb.button(text="Подтвердить", callback_data="confirm")
    kb.button(text="Назад", callback_data="back")
    kb.adjust(2)

    await callback.message.answer(text, reply_markup=kb.as_markup())
    await state.set_state(OrderState.checkout)

@dp.callback_query(lambda c: c.data == "back")
async def go_back(callback: CallbackQuery, state: FSMContext):
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
    rows.append([types.InlineKeyboardButton(text="Корзина", callback_data="cart")])
    builder.inline_keyboard = rows

    await callback.message.answer("Выберите товар:", reply_markup=builder.as_markup())
    await state.set_state(OrderState.choosing)

@dp.callback_query(lambda c: c.data == "confirm")
async def confirm(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    order = user_orders.get(user_id, {})
    contact = user_contacts[user_id].get("phone", "неизвестен")
    location = user_contacts[user_id].get("location", "неизвестна")

    text = f"Новый заказ от пользователя {user_id}:
Контакт: {contact}
Локация: {location}

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

    await bot.send_message(chat_id=ADMIN_ID, text=text)
    await callback.message.answer("Спасибо за заказ! Мы скоро свяжемся с вами.")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
