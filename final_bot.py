
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
    choosing = State()
    quantity = State()
    checkout = State()
    waiting_contact_location = State()

user_orders = {}
user_contacts = {}

@dp.message(lambda message: message.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    user_orders[message.from_user.id] = {}
    kb = InlineKeyboardBuilder()
    for key, item in products.items():
        kb.button(text=item["name"], callback_data=f"product:{key}")
    await message.answer("""
🥳 Вас приветствует бот <b>Oson hayot</b>!

🚚 Бесплатная доставка нужных веществ до вашего дома
📶 Качество вещей на вышем уровне
⏰ Доставка с 10:00 до 23:00
☎️ Call центр: +998(98)888-81-10
⌛️ Доставка в течение часа

🟦 Отправьте контакт чтобы продолжить.
""", parse_mode="HTML", reply_markup=kb.as_markup())
    await state.set_state(OrderState.choosing)

@dp.callback_query(lambda c: c.data.startswith("product:"))
async def select_product(callback: CallbackQuery, state: FSMContext):
    product_key = callback.data.split(":")[1]
    await state.update_data(product_key=product_key)
    kb = InlineKeyboardBuilder()
    for i in range(1, 11):
        kb.button(text=str(i), callback_data=f"qty:{i}")
    await callback.message.edit_text(f"Сколько штук '{products[product_key]['name']}' вы хотите?", reply_markup=kb.as_markup())
    await state.set_state(OrderState.quantity)

@dp.callback_query(lambda c: c.data.startswith("qty:"))
async def select_quantity(callback: CallbackQuery, state: FSMContext):
    qty = int(callback.data.split(":")[1])
    data = await state.get_data()
    product_key = data["product_key"]
    user_id = callback.from_user.id
    user_orders[user_id][product_key] = qty
    await callback.message.answer(f"Добавлено: {products[product_key]['name']} - {qty} шт.")
    
    kb = InlineKeyboardBuilder()
    for key, item in products.items():
        kb.button(text=item["name"], callback_data=f"product:{key}")
    kb.button(text="Перейти к чеку", callback_data="checkout")
    await callback.message.answer("Выберите следующий товар или перейдите к чеку:", parse_mode="HTML", reply_markup=kb.as_markup())
    await state.set_state(OrderState.choosing)

@dp.callback_query(lambda c: c.data == "checkout")
async def show_checkout(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    order = user_orders.get(user_id, {})
    text = "<b>Ваш чек:</b>\n\n"
    total = 0
    for key, qty in order.items():
        item = products[key]
        price = item["price"] * qty
        total += price
        text += f"{item['name']} — {qty} шт. = {price:,} сум\n"
    text += f"\n<b>Общая сумма: {total:,} сум</b>"

    contact_btn = KeyboardButton(text="Отправить номер", request_contact=True)
    location_btn = KeyboardButton(text="Отправить геолокацию", request_location=True)
    contact_kb = ReplyKeyboardMarkup(keyboard=[[contact_btn], [location_btn]], resize_keyboard=True, one_time_keyboard=True)

    await callback.message.answer("Пожалуйста, отправьте ваш номер и геолокацию перед подтверждением:", parse_mode="HTML", reply_markup=contact_kb)
    await callback.message.answer(text, reply_markup=ReplyKeyboardRemove())
    await state.set_state(OrderState.waiting_contact_location)

@dp.message(lambda message: message.contact or message.location)
async def receive_contact_location(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in user_contacts:
        user_contacts[user_id] = {}
    if message.contact:
        user_contacts[user_id]["phone"] = message.contact.phone_number
    if message.location:
        user_contacts[user_id]["location"] = f"{message.location.latitude},{message.location.longitude}"

    if "phone" in user_contacts[user_id] and "location" in user_contacts[user_id]:
        kb = InlineKeyboardBuilder()
        kb.button(text="Подтвердить", callback_data="confirm")
        kb.button(text="Назад", callback_data="back")
        await message.answer("Теперь вы можете подтвердить заказ:", parse_mode="HTML", reply_markup=kb.as_markup())
        await state.set_state(OrderState.checkout)

@dp.callback_query(lambda c: c.data == "back")
async def back_to_selection(callback: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    for key, item in products.items():
        kb.button(text=item["name"], callback_data=f"product:{key}")
    kb.button(text="Перейти к чеку", callback_data="checkout")
    await callback.message.answer("Выберите товар:", parse_mode="HTML", reply_markup=kb.as_markup())
    await state.set_state(OrderState.choosing)

@dp.callback_query(lambda c: c.data == "confirm")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    order = user_orders.get(user_id, {})
    contact = user_contacts.get(user_id, {}).get("phone", "Не предоставлен")
    location = user_contacts.get(user_id, {}).get("location", "Не предоставлена")

    text = f"Новый заказ от <a href='tg://user?id={user_id}'>пользователя</a>:\n\n"
    total = 0
    for key, qty in order.items():
        item = products[key]
        price = item["price"] * qty
        total += price
        text += f"{item['name']} — {qty} шт. = {price:,} сум\n"
    text += f"\n<b>Общая сумма: {total:,} сум</b>\n"
    text += f"\nКонтакт: {contact}\nЛокация: {location}"

    await bot.send_message(chat_id=ADMIN_ID, text=text)
    await callback.message.answer("Спасибо за заказ! Мы свяжемся с вами.")
    user_orders[user_id] = {}
    user_contacts[user_id] = {}
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
