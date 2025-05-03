# final_bot.py
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

# Включаем логирование для получения информации о работе бота
logging.basicConfig(level=logging.INFO)

# Укажите токен вашего бота
BOT_TOKEN = "8197970222:AAGotKTpT8t9ZSli6VbJKhPxNAWTKI2q7j8"

# ID администратора, которому будет отправляться информация о заказе
ADMIN_ID = 6497374401

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Список товаров (название и цена)
PRODUCTS = [
    {"name": "Яйца на флейке (30шт)", "price": 40000},
    {"name": "Вода 5 литров", "price": 6000},
    {"name": "Вода 10 литров", "price": 11000},
    {"name": "Картошка 1 кг", "price": 15000},
    {"name": "Сахар 1 кг", "price": 20000},
    {"name": "Масло 1 л", "price": 25000},
]

# Глобальное хранилище данных пользователя (контакт, локация, корзина)
user_data = {}

# Клавиатура для запроса контакта (кнопка "Отправить номер")
contact_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
contact_kb.add(KeyboardButton("Отправить номер", request_contact=True))

# Клавиатура для запроса геолокации (кнопка "Отправить геолокацию")
location_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
location_kb.add(KeyboardButton("Отправить геолокацию", request_location=True))

# Клавиатура со списком товаров (inline-кнопки товаров и кнопка "Корзина")
product_kb = InlineKeyboardMarkup(row_width=1)
for idx, prod in enumerate(PRODUCTS, start=1):
    # Формируем подпись кнопки: "Название товара: цена"
    button_text = f"{prod['name']}: {prod['price']:,} сум"
    product_kb.add(InlineKeyboardButton(button_text, callback_data=f"product_{idx}"))
# Добавляем кнопку "Корзина" для просмотра заказа
product_kb.add(InlineKeyboardButton("Корзина", callback_data="view_cart"))

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Приветствие и запрос контакта пользователя
    await message.answer(
        "Здравствуйте! Добро пожаловать в наш бот-магазин.\n"
        "Для продолжения отправьте свой номер телефона кнопкой ниже.",
        reply_markup=contact_kb
    )

# Обработчик получения контакта пользователя
@dp.message(lambda message: message.contact is not None)
async def handle_contact(message: types.Message):
    user_id = message.from_user.id
    contact = message.contact
    # Сохраняем имя и телефон пользователя
    name = contact.first_name
    if contact.last_name:
        name += f" {contact.last_name}"
    phone = contact.phone_number
    user_data[user_id] = {
        "name": name,
        "phone": phone,
        "cart": {}
    }
    # Запрашиваем геолокацию пользователя
    await message.answer(
        "Спасибо! Теперь отправьте свою геолокацию кнопкой ниже.",
        reply_markup=location_kb
    )

# Обработчик получения геолокации пользователя
@dp.message(lambda message: message.location is not None)
async def handle_location(message: types.Message):
    user_id = message.from_user.id
    location = message.location
    lat = location.latitude
    lon = location.longitude
    # Сохраняем локацию пользователя
    if user_id in user_data:
        user_data[user_id]["location"] = (lat, lon)
    else:
        # Если по какой-то причине данных пользователя ещё нет, создаём запись
        user_data[user_id] = {"location": (lat, lon), "cart": {}}
    # Отправляем список товаров с ценами и кнопками для выбора
    await message.answer(
        "Выберите товар из списка ниже:",
        reply_markup=product_kb
    )

# Обработчик выбора товара (нажатие на кнопку товара)
@dp.callback_query(lambda c: c.data and c.data.startswith("product_"))
async def on_product_selected(callback: types.CallbackQuery):
    # Извлекаем индекс товара из callback_data, например "product_2" -> 2
    prod_idx = int(callback.data.split('_')[1])
    product = PRODUCTS[prod_idx - 1]
    # Генерируем inline-клавиатуру для выбора количества (1-10) и кнопок "Назад" и "Корзина"
    quant_kb = InlineKeyboardMarkup(row_width=5)
    for q in range(1, 11):
        quant_kb.add(InlineKeyboardButton(str(q), callback_data=f"qty_{prod_idx}_{q}"))
    # Кнопки "Назад" и "Корзина" на новой строке
    quant_kb.add(InlineKeyboardButton("Назад", callback_data="back_to_menu"))
    quant_kb.add(InlineKeyboardButton("Корзина", callback_data="view_cart"))
    # Обновляем сообщение: просим выбрать количество для выбранного товара
    await callback.message.edit_text(
        f"Вы выбрали: {product['name']}.\nВыберите количество:",
        reply_markup=quant_kb
    )
    # Подтверждаем получение колбэка (убираем индикатор загрузки на кнопке)
    await callback.answer()

# Обработчик выбора количества товара
@dp.callback_query(lambda c: c.data and c.data.startswith("qty_"))
async def on_quantity_selected(callback: types.CallbackQuery):
    # Пример callback.data: "qty_2_5" (товар 2, количество 5)
    parts = callback.data.split('_')
    prod_idx = int(parts[1])
    quantity = int(parts[2])
    product = PRODUCTS[prod_idx - 1]
    user_id = callback.from_user.id
    # Добавляем товар в корзину (суммируем количество, если товар уже есть)
    if user_id not in user_data:
        user_data[user_id] = {"cart": {}}
    cart = user_data[user_id].setdefault("cart", {})
    if prod_idx in cart:
        cart[prod_idx] += quantity
    else:
        cart[prod_idx] = quantity
    # Краткое уведомление о добавлении товара в корзину
    await callback.answer(f'Добавлено в корзину: {quantity} шт. "{product["name"]}"')
    # (Пользователь может добавить другие товары или открыть корзину с помощью кнопок)

# Обработчик кнопки "Назад" (возврат к списку товаров)
@dp.callback_query(lambda c: c.data == "back_to_menu")
async def on_back_to_menu(callback: types.CallbackQuery):
    # Возвращаемся к списку товаров
    await callback.message.edit_text(
        "Выберите товар из списка ниже:",
        reply_markup=product_kb
    )
    await callback.answer()

# Обработчик кнопки "Корзина" (просмотр содержимого корзины)
@dp.callback_query(lambda c: c.data == "view_cart")
async def on_view_cart(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    cart = user_data.get(user_id, {}).get("cart", {})
    if not cart:
        # Если корзина пуста, уведомляем пользователя
        await callback.answer("Ваша корзина пуста.", show_alert=True)
        return
    # Формируем текст чека с перечнем товаров
    receipt_lines = []
    total_sum = 0
    for prod_idx, qty in cart.items():
        product = PRODUCTS[prod_idx - 1]
        price = product['price']
        item_sum = price * qty
        total_sum += item_sum
        # Строка вида: "Название товара - X шт x Y сум = Z сум"
        line = f"{product['name']} - {qty} шт x {price:,} сум = {item_sum:,} сум"
        receipt_lines.append(line)
    receipt_text = "Ваш заказ:\n" + "\n".join(receipt_lines) + f"\nОбщая сумма: {total_sum:,} сум"
    # Клавиатура с кнопками "Подтвердить" и "Назад"
    cart_kb = InlineKeyboardMarkup()
    cart_kb.add(InlineKeyboardButton("Подтвердить", callback_data="confirm_order"))
    cart_kb.add(InlineKeyboardButton("Назад", callback_data="back_to_menu"))
    # Обновляем сообщение: показываем содержимое корзины (чек)
    await callback.message.edit_text(receipt_text, reply_markup=cart_kb)
    await callback.answer()

# Обработчик кнопки "Подтвердить" (оформление заказа)
@dp.callback_query(lambda c: c.data == "confirm_order")
async def on_confirm_order(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    cart = user_data.get(user_id, {}).get("cart", {})
    if not cart:
        await callback.answer("Корзина пуста.", show_alert=True)
        return
    # Подготовка данных заказа для отправки администратору
    name = user_data.get(user_id, {}).get("name", "")
    phone = user_data.get(user_id, {}).get("phone", "")
    location = user_data.get(user_id, {}).get("location", None)
    # Формируем сообщение с информацией о заказе
    order_lines = []
    total_sum = 0
    for prod_idx, qty in cart.items():
        product = PRODUCTS[prod_idx - 1]
        price = product['price']
        item_sum = price * qty
        total_sum += item_sum
        order_lines.append(f"{product['name']} - {qty} шт x {price:,} сум = {item_sum:,} сум")
    order_text = "\n".join(order_lines) + f"\nОбщая сумма: {total_sum:,} сум"
    admin_message = (
        f"Новый заказ!\n"
        f"Имя пользователя: {name}\n"
        f"Номер телефона: {phone}\n"
    )
    if location:
        lat, lon = location
        admin_message += f"Локация: {lat}, {lon}\n"
    admin_message += "Состав заказа:\n" + order_text
    # Отправляем информацию о заказе администратору
    try:
        if location:
            await bot.send_location(ADMIN_ID, latitude=lat, longitude=lon)
        await bot.send_message(ADMIN_ID, admin_message)
    except Exception as e:
        logging.error(f"Не удалось отправить сообщение администратору: {e}")
    # Уведомляем пользователя о подтверждении заказа
    await callback.message.edit_text("Спасибо! Ваш заказ подтвержден и отправлен администратору.", reply_markup=None)
    await callback.answer()
    # Очищаем корзину пользователя (для возможного нового заказа)
    user_data[user_id]["cart"] = {}

# Запуск бота
async def main():
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
