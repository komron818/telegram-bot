from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.enums import ParseMode
import asyncio

API_TOKEN = '8197970222:AAGotKTpT8t9ZSli6VbJKhPxNAWTKI2q7j8'
ADMIN_ID = 6497374401

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

class OrderState(StatesGroup):
    choosing_product = State()

products = {
    "Яйца": 40000,
    "Вода 5 л": 6000,
    "Вода 10 л": 11000,
    "Картошка": 15000,
    "Сахар": 20000,
    "Масло": 25000
}

user_orders = {}

@dp.message(lambda message: message.text == "/start")
async def start(message: Message, state: FSMContext):
    user_orders[message.from_user.id] = {}
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=key) for key in list(products.keys())[:3]],
            [KeyboardButton(text=key) for key in list(products.keys())[3:]],
            [KeyboardButton(text="Корзина")]
        ],
        resize_keyboard=True
    )
    await message.answer("Добро пожаловать в бот Oson hayot!
Выберите товар:", reply_markup=kb)
    await state.set_state(OrderState.choosing_product)

@dp.message(OrderState.choosing_product)
async def handle_product(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text

    if text == "Корзина":
        order = user_orders.get(user_id, {})
        if not order:
            await message.answer("Ваша корзина пуста.")
            return
        summary = "Ваш чек:

"
        total = 0
        for name, qty in order.items():
            price = products[name]
            cost = price * qty
            total += cost
            summary += f"{name} — {qty} шт. = {cost:,} сум\n"
        summary += f"\nОбщая сумма: {total:,} сум"

        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Подтвердить")], [KeyboardButton(text="Назад")]],
            resize_keyboard=True
        )
        await message.answer(summary, reply_markup=kb)
        await bot.send_message(ADMIN_ID, f"Новый заказ от пользователя {user_id}:

{summary}")
        return

    if text in products:
        user_orders[user_id][text] = user_orders[user_id].get(text, 0) + 1
        await message.answer(f"Добавлено: {text} — 1 шт.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())