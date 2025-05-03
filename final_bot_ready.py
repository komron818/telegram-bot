from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types
import asyncio
import logging

TOKEN = "8197970222:AAGotKTpT8t9ZSli6VbJKhPxNAWTKI2q7j8"
ADMIN_ID = 6497374401

bot = Bot(token=TOKEN)
dp = Dispatcher()

router = Router()
dp.include_router(router)

logging.basicConfig(level=logging.INFO)

class OrderState(StatesGroup):
    waiting_for_contact = State()
    waiting_for_location = State()
    choosing_product = State()
    choosing_quantity = State()
    reviewing_order = State()

products = {
    "Яйца (30 шт)": 40000,
    "Вода 5л": 6000,
    "Вода 10л": 11000,
    "Картошка 1кг": 15000,
    "Сахар 1кг": 20000,
    "Масло 1л": 25000
}

user_orders = {}
user_data = {}

@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    user_orders[message.chat.id] = []
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить номер", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("Пожалуйста, отправьте свой номер телефона:", reply_markup=kb)
    await state.set_state(OrderState.waiting_for_contact)

@router.message(F.contact)
async def receive_contact(message: Message, state: FSMContext):
    user_data[message.chat.id] = {"phone": message.contact.phone_number}
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить локацию", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("Теперь отправьте локацию доставки:", reply_markup=kb)
    await state.set_state(OrderState.waiting_for_location)

@router.message(F.location)
async def receive_location(message: Message, state: FSMContext):
    user_data[message.chat.id]["location"] = message.location
    await show_products(message)
    await state.set_state(OrderState.choosing_product)

async def show_products(message: Message):
    buttons = [types.InlineKeyboardButton(text=name, callback_data=name) for name in products]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[btn] for btn in buttons] + [[
        types.InlineKeyboardButton(text="Корзина", callback_data="cart")
    ]])
    await message.answer("Выберите товар:", reply_markup=keyboard)

@router.callback_query(F.data.in_(products.keys()))
async def select_product(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(selected_product=callback.data)
    buttons = [InlineKeyboardButton(text=str(i), callback_data=f"qty_{i}") for i in range(1, 11)]
    kb = InlineKeyboardMarkup(inline_keyboard=[buttons[i:i+5] for i in range(0, 10, 5)] + [[
        InlineKeyboardButton(text="Назад", callback_data="back")
    ]])
    await callback.message.answer(f"Сколько штук '{callback.data}' вы хотите?", reply_markup=kb)

@router.callback_query(F.data.startswith("qty_"))
async def add_to_cart(callback: types.CallbackQuery, state: FSMContext):
    qty = int(callback.data.split("_")[1])
    data = await state.get_data()
    product = data["selected_product"]
    user_orders[callback.from_user.id].append((product, qty))
    await show_products(callback.message)

@router.callback_query(F.data == "cart")
async def show_cart(callback: types.CallbackQuery):
    items = user_orders.get(callback.from_user.id, [])
    if not items:
        await callback.message.answer("Ваша корзина пуста.")
        return
    total = 0
    text = "<b>Корзина:</b>\n"
    for item, qty in items:
        price = products[item] * qty
        text += f"{item} — {qty} шт. = {price:,} сум\n"
        total += price
    text += f"\n<b>Общая сумма: {total:,} сум</b>"
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Подтвердить", callback_data="confirm"),
        InlineKeyboardButton(text="Назад", callback_data="back")
    ]])
    await callback.message.answer(text, reply_markup=kb)

@router.callback_query(F.data == "confirm")
@router.callback_query(F.data == "confirm")
async def confirm_order(callback: types.CallbackQuery):
    items = user_orders.get(callback.from_user.id, [])
    data = user_data.get(callback.from_user.id, {})
    text = "Новый заказ:\n"
    for item, qty in items:
        text += f"{item} — {qty} шт.\n"
    text += f"\nТелефон: {data.get('phone')}"
    loc = data.get("location")
    if loc:
        text += f"\nЛокация: https://www.google.com/maps?q={loc.latitude},{loc.longitude}"
    await bot.send_message(ADMIN_ID, text)
    await callback.message.answer("Спасибо! Ваш заказ был принят.")

@router.callback_query(F.data == "back")
async def back_to_products(callback: types.CallbackQuery):
    await show_products(callback.message)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())