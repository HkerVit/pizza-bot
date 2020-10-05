from textwrap import dedent

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from more_itertools import chunked

import moltin
import closest_pizzeria



def get_menu_keyboard(products, menu_page_number):
    products_menu_page = list(chunked(products, 6))
    if menu_page_number < 0:
        menu_page_number = len(products_menu_page) - 1
    if menu_page_number >= len(products_menu_page):
        menu_page_number = 0

    products_keyboard = [
        [InlineKeyboardButton(product['name'], callback_data=product['id'])] for product in products_menu_page[menu_page_number]
        ]
    products_keyboard.append([InlineKeyboardButton('<--', callback_data='-1'),
                              InlineKeyboardButton('-->', callback_data='1')])
    products_keyboard.append([InlineKeyboardButton('Корзина', callback_data='cart')])
    return InlineKeyboardMarkup(products_keyboard), menu_page_number


def get_product_keyboard_and_text(products, product_id, token):
    product = next((product for product in products if product['id'] == product_id))
    image = moltin.get_image_url(token, product['image_id'])

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
    cart = moltin.get_cart_items(token, chat_id)
    message = ''
    keyboard = []
    for product in cart['items']:
        keyboard.append([InlineKeyboardButton(f"Убрать из корзины {product['name']}", callback_data=f"remove,{product['id']}")])

        product_output = dedent(f'''
            Пицца {product['name']}
            {product['description']}
            По цене {product['price']} руб

            В заказе {product['quantity']} за {product['amount']} руб
            ''')
        message += product_output

    keyboard.append([InlineKeyboardButton('Меню', callback_data='menu')])
    keyboard.append([InlineKeyboardButton('Выбор доставки', callback_data='delivery_choice')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    message += f'\nВсего к оплате: {cart["total_amount"]} руб'

    return reply_markup, message, cart


def get_location_keyboard_and_text(token, lon, lat):
    pizzerias = moltin.get_all_entries(token)    
    pizzeria = closest_pizzeria.get_closest_pizzeria(lon, lat, pizzerias)

    if pizzeria['distance'] > 20:
        distance = int(pizzeria['distance'])
        message = dedent(f'''
        К сожалению Вы находитесь далеко от нас,
        Ближайшая пиццерия аж в {distance} км от Вас!
        ''')
        keyboard = [
            [InlineKeyboardButton('Завершить заказ', callback_data='close')],
            [InlineKeyboardButton('Изменить заказ', callback_data='cart')]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton('Самовывоз', callback_data='self')],
            [InlineKeyboardButton('Доставка', callback_data='delivery')]
        ]
        if pizzeria['distance'] <= 0.5:
            distance = int(pizzeria['distance'] * 1000)
            message = dedent(f'''
            Может заберёте пиццу из нашей пиццерии неподалеку? 
            Она всего в {distance} метров от Вас! Вот ее адрес: {pizzeria["address"]}. 
            Но можем доставить и бесплатно! Нам не сложно)''')

        elif pizzeria['distance'] <= 5:
            message = dedent('''
            Похоже придется ехать до Вас на самокате. 
            Доставка будет стоить 100 руб. 
            Доставляем или самовывоз?''')
        else:
            message = dedent(f'''
            Вы довольно далеко от нас. Ближайшая к вам пиццерия
            находится по адресу: {pizzeria["address"]}. Доставка будет стоить 300 руб.
            Но Вы можете забрать пиццу самостоятельно)''')
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    return reply_markup, message, pizzeria


def get_delivery_keyboard_and_text(token, query, pizzeria, cart):
    chat_id = query.message.chat_id

    moltin.fill_customer_fields(chat_id, pizzeria['client_lat'], pizzeria['client_lon'], token)

    message = 'Спасибо за выбор нашей пиццы!\n'
    if query.data == 'self':
        lat = pizzeria['lat']
        lon = pizzeria['lon']
        self_delivery_message = dedent(f'''
        Ближайшая к вам пиццерия находится по адресу: 
        {pizzeria['address']}\n
        ''')
        message += self_delivery_message

    order_message = 'Ваш заказ:\n'
    for product in cart['items']:
        order = dedent(f'''
            Пицца {product['name']}
            {product['description']}
            По цене {product['price']} руб - {product['quantity']} шт

            ''')
        order_message += order
    message = message + order_message + f'Всего к оплате: {cart["total_amount"]} руб'
    keyboard = [
        [InlineKeyboardButton('Оплата наличными', callback_data='cash')],
        [InlineKeyboardButton('Оплата картой', callback_data='card')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    delivery_message = dedent(f'''
    Получен заказ:
    {order_message} Доставка вот по этому адресу
    ''')

    return reply_markup, message, delivery_message