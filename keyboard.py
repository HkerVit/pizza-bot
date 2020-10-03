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


def get_product_keyboard(products, product_id, token):
    product = next((product for product in products if product['id'] == product_id))
    image = moltin_bot_function.get_image_url(token, product['image_id'])

    product_keyboard = [
        [InlineKeyboardButton(f'Выбрать - {product["name"]}', callback_data=f'{product_index}')],
        [InlineKeyboardButton('Меню', callback_data='menu')],
        ]
    reply_markup = InlineKeyboardMarkup(product_keyboard)
    message = dedent(f'''
    {product['name']}\n
    {product['price']} руб\n
    {product['description']}
    ''')

    return reply_markup, message, image