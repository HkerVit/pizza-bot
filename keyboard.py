from textwrap import dedent

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from more_itertools import chunked

import moltin_bot_function



def get_menu_keyboard(products, menu_page_number):
    products_menu_page = list(chunked(products, 6))
    if menu_page_number < 0:
        menu_page_number = len(products_menu_page) - 1
    if menu_page_number >= len(products_menu_page):
        menu_page_number = 0

    products_keyboard = [
        [InlineKeyboardButton(product['name'], callback_data=product['id'])] for product in products_menu_page[menu_page_number]
        ]
    products_keyboard.append([InlineKeyboardButton('<--', callback_data='prev'),
                              InlineKeyboardButton('-->', callback_data='next')])
    products_keyboard.append([InlineKeyboardButton('Корзина', callback_data='cart')])
    return InlineKeyboardMarkup(products_keyboard)


def get_product_keyboard_and_text(products, product_id, token):
    product = next((product for product in products if product['id'] == product_id))
    image = moltin_bot_function.get_image_url(token, product['image_id'])

    product_keyboard = [
        [InlineKeyboardButton(f'Выбрать - {product["name"]}', callback_data=f'{product_id}')],
        [InlineKeyboardButton('Меню', callback_data='menu')],
        ]
    reply_markup = InlineKeyboardMarkup(product_keyboard)
    message = dedent(f'''
    {product['name']}\n
    {product['price']} руб\n
    {product['description']}
    ''')

    return reply_markup, message, image


def get_cart_keyboard_and_text(token, chat_id):
    cart, total_amount = moltin_bot_function.get_cart_items(token, chat_id)
    message = ''
    cart_keyboard = []
    for product in cart:
        cart_keyboard.append([InlineKeyboardButton(f"Убрать из корзины {product['name']}", callback_data=f"remove,{product['id']}")])

        product_output = dedent(f'''
            Пицца {product['name']}
            {product['description']}
            По цене {product['price']} руб

            В заказе {product['quantity']} за {product['amount']} руб
            ''')
        message += product_output

    cart_keyboard.append([InlineKeyboardButton('Меню', callback_data='menu')])
    cart_keyboard.append([InlineKeyboardButton('Выбор доставки', callback_data='delivery_choice')])
    reply_markup = InlineKeyboardMarkup(cart_keyboard)
    message += f'\nВсего к оплате: {total_amount} руб'

    return reply_markup, message, cart, total_amount