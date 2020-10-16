from textwrap import dedent

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from more_itertools import chunked

import moltin
import closest_pizzeria


def get_menu_keyboard(chat_id, products, menu_navigation):
    products_menu_pages = list(chunked(products, 6))
    max_page_index = len(products_menu_pages) - 1

    if menu_navigation == '/start' or menu_navigation == 'menu':
        page_number = 0
    else:
        page_number = int(menu_navigation.split(',')[1])
    
    prev_page = page_number - 1
    next_page = page_number + 1
    if prev_page < 0:
        prev_page = max_page_index
    elif next_page > max_page_index:
        next_page = 0
            
    products_keyboard = [
        [InlineKeyboardButton(product['name'], callback_data=product['id'])] 
        for product 
        in products_menu_pages[page_number]
    ]
    products_keyboard.append([InlineKeyboardButton('<--', callback_data=f'prev,{prev_page}'),
                              InlineKeyboardButton('-->', callback_data=f'next,{next_page}')])
    products_keyboard.append([InlineKeyboardButton('Корзина', callback_data='cart')])
    return InlineKeyboardMarkup(products_keyboard)


def get_product_reply(products, product_id, token):
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


def get_cart_reply(token, chat_id):
    cart = moltin.get_cart_items(token, chat_id)
    message = ''
    keyboard = []
    for product in cart['items']:
        keyboard.append(
            [InlineKeyboardButton(f"Убрать из корзины {product['name']}", callback_data=f"remove,{product['id']}")])

        product_output = dedent(f'''
            Пицца {product['name']}
            {product['description']}
            По цене {product['price']} руб

            У вас {product['quantity']} за {product['amount']} руб''')
        message = dedent(f'''{message}
        {product_output}''')

    keyboard.append([InlineKeyboardButton('Меню', callback_data='menu')])
    keyboard.append([InlineKeyboardButton('Выбор доставки', callback_data='delivery_choice')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = dedent(f'''
    {message}\n\nВсего к оплате: {cart["total_amount"]} руб''')

    return reply_markup, message, cart


def get_location_reply(token, lon, lat):
    pizzerias = moltin.get_all_pizzerias(token)
    pizzeria = closest_pizzeria.get_closest_pizzeria(lon, lat, pizzerias)
    pizzeria['customer_lon'] = lon
    pizzeria['customer_lat'] = lat

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
        delivery_fee = -1
    else:
        keyboard = [
            [InlineKeyboardButton('Самовывоз', callback_data='self')],
            [InlineKeyboardButton('Доставка', callback_data='delivery')]
        ]
        if pizzeria['distance'] <= 0.5:
            meter_in_km = 1000
            distance_in_meter = int(pizzeria['distance'] * meter_in_km)
            message = dedent(f'''
            Может заберёте пиццу из нашей пиццерии неподалеку? 
            Она всего в {distance_in_meter} метров от Вас! Вот ее адрес: {pizzeria["address"]}.\n
            Но можем доставить и бесплатно! Нам не сложно)''')
            delivery_fee = 0

        elif pizzeria['distance'] <= 5:
            message = dedent('''
            Похоже придется ехать до Вас на самокате. 
            Доставка будет стоить 100 руб.\n
            Доставляем или самовывоз?''')
            delivery_fee = 100
        else:
            message = dedent(f'''
            Вы довольно далеко от нас. Ближайшая к вам пиццерия
            находится по адресу: {pizzeria["address"]}.
            Доставка будет стоить 300 руб.\n
            Доставляем или самовывоз?''')
            delivery_fee = 300

    reply_markup = InlineKeyboardMarkup(keyboard)

    return reply_markup, message, pizzeria, delivery_fee


def get_delivery_reply(token, query, pizzeria, cart):
    chat_id = query.message.chat_id

    moltin.fill_customer_fields(chat_id, pizzeria['customer_lat'], pizzeria['customer_lon'], token)

    message = 'Спасибо за выбор нашей пиццы!\n'
    if query.data == 'self':
        self_delivery_message = dedent(f'''
        Ближайшая к вам пиццерия находится по адресу: 
        {pizzeria['address']}\n
        ''')
        message += self_delivery_message
        cart['delivery'] = False

    order_message = ''
    for product in cart['items']:
        order = dedent(f'''
            Пицца {product['name']}
            {product['description']}
            По цене {product['price']} руб - {product['quantity']} шт\n\n''')
        order_message += order

    if query.data == 'delivery':
        cart['delivery'] = True
        if cart['delivery_fee'] > 0:
            order_message += f'Стоимость доставки - {cart["delivery_fee"]} руб\n'
            cart['total_amount'] = cart['total_amount'] + cart['delivery_fee']

    message = dedent(f'''{message}Ваш заказ:
    {order_message}Всего к оплате: {cart["total_amount"]} руб''')

    keyboard = [
        [InlineKeyboardButton('Оплата наличными', callback_data='cash')],
        [InlineKeyboardButton('Оплата картой', callback_data='card')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    delivery_message = dedent(f'''
    Оплачен заказ:
    {order_message}Итого к оплате {cart["total_amount"]} руб. 
    Доставка по этому адресу:
    ''')

    cart['delivery_message'] = delivery_message

    return reply_markup, message, cart
