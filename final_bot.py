# final_bot.py
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# Enable logging
logging.basicConfig(level=logging.INFO)

# Bot token and admin ID
TOKEN = "8197970222:AAGotKTpT8t9ZSli6VbJKhPxNAWTKI2q7j8"
ADMIN_ID = 6497374401

# Define FSM states
class OrderFSM(StatesGroup):
    contact = State()
    location = State()
    product = State()
    quantity = State()
    checkout = State()

# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Products list with names and prices
PRODUCTS = {
    "Яйца на флейке (30шт): 40000 сум": {"name": "Яйца на флейке (30шт)", "price": 40000},
    "Вода 5 литров: 6000 сум": {"name": "Вода 5 литров", "price": 6000},
    "Вода 10 литров: 11000 сум": {"name": "Вода 10 литров", "price": 11000},
    "Картошка 1 кг: 15000 сум": {"name": "Картошка 1 кг", "price": 15000},
    "Сахар 1 кг: 20000 сум": {"name": "Сахар 1 кг", "price": 20000},
    "Масло 1 литр: 25000 сум": {"name": "Масло 1 литр", "price": 25000}
}

# /start command handler
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    # Reset any previous state and data
    await state.clear()
    # Request contact with keyboard
    contact_btn = KeyboardButton("Отправить номер", request_contact=True)
    contact_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(contact_btn)
    await message.answer("Привет! Пожалуйста, отправьте свой номер телефона:", reply_markup=contact_kb)
    # Set state to wait for contact
    await state.set_state(OrderFSM.contact)

# Contact message handler
@dp.message(OrderFSM.contact)
async def handle_contact(message: types.Message, state: FSMContext):
    # Ensure the user sent a contact
    if message.contact is None:
        # If not, ask again for contact
        contact_btn = KeyboardButton("Отправить номер", request_contact=True)
        contact_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(contact_btn)
        await message.answer("Пожалуйста, отправьте свой номер через кнопку ниже.", reply_markup=contact_kb)
        return
    # Save phone number (and optionally user name)
    phone_number = message.contact.phone_number
    await state.update_data(phone=phone_number)
    # Request location with keyboard
    location_btn = KeyboardButton("Отправить локацию", request_location=True)
    location_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(location_btn)
    await message.answer("Спасибо! Теперь отправьте свою геолокацию:", reply_markup=location_kb)
    # Set state to wait for location
    await state.set_state(OrderFSM.location)

# Location message handler
@dp.message(OrderFSM.location)
async def handle_location(message: types.Message, state: FSMContext):
    # Ensure the user sent a location
    if message.location is None:
        location_btn = KeyboardButton("Отправить локацию", request_location=True)
        location_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(location_btn)
        await message.answer("Пожалуйста, отправьте геолокацию через кнопку ниже.", reply_markup=location_kb)
        return
    # Save location (latitude, longitude)
    await state.update_data(location=(message.location.latitude, message.location.longitude))
    # Show product list with keyboard
    product_kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for item in PRODUCTS.keys():
        product_kb.add(KeyboardButton(item))
    await message.answer("Выберите товар из списка:", reply_markup=product_kb)
    # Set state to product selection
    await state.set_state(OrderFSM.product)

# Product selection handler
@dp.message(OrderFSM.product)
async def handle_product_selection(message: types.Message, state: FSMContext):
    product_text = message.text
    # Check if the selected text is a valid product
    if product_text not in PRODUCTS:
        await message.answer("Пожалуйста, выберите товар, используя кнопки.")
        return
    # Save selected product details
    selected = PRODUCTS[product_text]
    await state.update_data(current_product_name=selected["name"], current_product_price=selected["price"])
    # Ask for quantity with keyboard 1-10 and options
    qty_kb = ReplyKeyboardMarkup(resize_keyboard=True)
    qty_kb.row(*[KeyboardButton(str(i)) for i in range(1, 6)])
    qty_kb.row(*[KeyboardButton(str(i)) for i in range(6, 11)])
    qty_kb.row(KeyboardButton("Добавить продукт"), KeyboardButton("Корзина"))
    qty_kb.add(KeyboardButton("Назад"))
    await message.answer(f"Выберите количество от 1 до 10 для {selected['name']}:", reply_markup=qty_kb)
    # Set state to quantity selection
    await state.set_state(OrderFSM.quantity)

# Quantity selection and cart management handler
@dp.message(OrderFSM.quantity)
async def handle_quantity_or_action(message: types.Message, state: FSMContext):
    user_input = message.text
    data = await state.get_data()
    # If user selected a number (1-10)
    if user_input.isdigit():
        qty = int(user_input)
        if 1 <= qty <= 10:
            # Save chosen quantity
            await state.update_data(current_quantity=qty)
            await message.answer(f"Количество {qty} шт. выбрано. Теперь вы можете добавить товар в корзину или открыть корзину для просмотра.")
            return
    # If user chose to add the product to cart
    if user_input == "Добавить продукт":
        current_product = data.get("current_product_name")
        current_price = data.get("current_product_price")
        current_qty = data.get("current_quantity")
        if current_product is None or current_price is None:
            await message.answer("Сначала выберите товар.")
            return
        if current_qty is None:
            await message.answer("Пожалуйста, выберите количество перед добавлением товара.")
            return
        # Add item to cart
        cart = data.get("cart", [])
        cart.append({"name": current_product, "price": current_price, "quantity": current_qty})
        await state.update_data(cart=cart)
        # Clear current selection variables
        await state.update_data(current_product_name=None, current_product_price=None, current_quantity=None)
        # Show product list again for next selection
        product_kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for item in PRODUCTS.keys():
            product_kb.add(KeyboardButton(item))
        await message.answer("Товар добавлен в корзину. Выберите следующий товар или откройте корзину для просмотра заказа.", reply_markup=product_kb)
        await state.set_state(OrderFSM.product)
        return
    # If user wants to view the cart
    if user_input == "Корзина":
        cart = data.get("cart", [])
        if not cart:
            await message.answer("Ваша корзина пока пуста. Добавьте хотя бы один товар.")
            return
        # Build the receipt text
        receipt_lines = ["Ваш заказ:"]
        total_sum = 0
        for item in cart:
            item_total = item["price"] * item["quantity"]
            total_sum += item_total
            receipt_lines.append(f"{item['name']}, {item['quantity']} шт, {item_total} сум")
        receipt_lines.append(f"Общая сумма: {total_sum} сум")
        receipt_text = "\n".join(receipt_lines)
        # Keyboard for confirming or going back
        cart_kb = ReplyKeyboardMarkup(resize_keyboard=True)
        cart_kb.add(KeyboardButton("Подтвердить"), KeyboardButton("Назад"))
        await message.answer(receipt_text, reply_markup=cart_kb)
        # Set state to checkout (confirmation stage)
        await state.set_state(OrderFSM.checkout)
        return
    # If user wants to go back to product selection without adding
    if user_input == "Назад":
        # Clear current product selection (not added to cart)
        await state.update_data(current_product_name=None, current_product_price=None, current_quantity=None)
        # Show product list again
        product_kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for item in PRODUCTS.keys():
            product_kb.add(KeyboardButton(item))
        await message.answer("Вы вернулись к списку товаров.", reply_markup=product_kb)
        await state.set_state(OrderFSM.product)
        return
    # If input is not recognized
    await message.answer("Пожалуйста, используйте кнопки для выбора количества или действия.")

# Checkout (cart confirmation) handler
@dp.message(OrderFSM.checkout)
async def handle_checkout(message: types.Message, state: FSMContext):
    user_input = message.text
    data = await state.get_data()
    if user_input == "Подтвердить":
        cart = data.get("cart", [])
        if not cart:
            await message.answer("Ваша корзина пуста.")
            return
        phone = data.get("phone", "")
        location = data.get("location")
        # Compose order summary for admin
        order_lines = [f"Новый заказ от пользователя {message.from_user.full_name}:"]
        for item in cart:
            item_total = item["price"] * item["quantity"]
            order_lines.append(f"{item['name']}, {item['quantity']} шт, {item_total} сум")
        total_sum = sum(item["price"] * item["quantity"] for item in cart)
        order_lines.append(f"Общая сумма: {total_sum} сум")
        order_lines.append(f"Телефон клиента: {phone}")
        if location:
            lat, lon = location
            order_lines.append(f"Координаты локации: {lat}, {lon}")
        order_text = "\n".join(order_lines)
        # Send order details to admin
        try:
            await bot.send_message(chat_id=ADMIN_ID, text=order_text)
            if location:
                lat, lon = location
                await bot.send_location(chat_id=ADMIN_ID, latitude=lat, longitude=lon)
        except Exception as e:
            logging.error(f"Failed to send order to admin: {e}")
        # Thank the user and clear keyboard
        await message.answer("Спасибо за заказ!", reply_markup=ReplyKeyboardRemove())
        # Clear state (end of order process)
        await state.clear()
    elif user_input == "Назад":
        # If user decides to continue shopping
        current_product = data.get("current_product_name")
        # If a product was in the process (selected but not added)
        if current_product:
            # Return to quantity selection for that product
            qty_kb = ReplyKeyboardMarkup(resize_keyboard=True)
            qty_kb.row(*[KeyboardButton(str(i)) for i in range(1, 6)])
            qty_kb.row(*[KeyboardButton(str(i)) for i in range(6, 11)])
            qty_kb.row(KeyboardButton("Добавить продукт"), KeyboardButton("Корзина"))
            qty_kb.add(KeyboardButton("Назад"))
            await message.answer(f"Продолжайте выбор количества для {current_product}:", reply_markup=qty_kb)
            await state.set_state(OrderFSM.quantity)
        else:
            # Return to product list to add more items
            product_kb = ReplyKeyboardMarkup(resize_keyboard=True)
            for item in PRODUCTS.keys():
                product_kb.add(KeyboardButton(item))
            await message.answer("Продолжайте выбор товаров.", reply_markup=product_kb)
            await state.set_state(OrderFSM.product)
    else:
        await message.answer("Пожалуйста, подтвердите заказ или вернитесь назад с помощью кнопок.")

# Start the bot
if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
