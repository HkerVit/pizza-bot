import logging
from textwrap import dedent
import time
import json

import redis
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from environs import Env
from more_itertools import chunked

from get_token import get_access_token
from manage_moltin_shop import get_products_list
from manage_moltin_shop import add_product_to_cart, remove_cart_items
from manage_moltin_shop import get_cart_items, create_customer
from manage_moltin_shop import get_image_url
from manage_moltin_shop import get_all_entries
from fetch_coordinates import fetch_coordinates
from distance import get_min_distance

env = Env()
env.read_env()

_database = None
moltin_token = None
moltin_token_expires = 0
menu_page_number = 0
products = []
pizzerias = []


def start(update, context):
    global products
    query = update.callback_query
    if query:
        chat_id = query.message.chat_id
    else:
        chat_id = update.message.chat_id

    check_access_token()
    if time.time() >= moltin_token_expires or len(products) == 0:
        moltin_product_info = get_products_list(token=moltin_token)
        fill_products_information(moltin_product_info)

    reply_markup = get_menu_keyboard(products)
    context.bot.send_message(chat_id=chat_id, text='Пожалуйста, выберите пиццу:',
                     reply_markup=reply_markup)
    if query:
        context.bot.delete_message(chat_id=chat_id, 
                           message_id=query.message.message_id)

    return 'HANDLE_MENU'


def handle_menu(update, context):
    check_access_token()
    query = update.callback_query
    chat_id = query.message.chat_id

    product_id = query.data
    product, product_index = get_product_by_id(product_id=product_id)
    image = get_image_url(token=moltin_token, image_id=product['image_id'])

    product_keyboard = [
        [InlineKeyboardButton('Положить в корзину', callback_data=f'{product_index}')],
        [InlineKeyboardButton('Корзина', callback_data='cart')],
        [InlineKeyboardButton('Меню', callback_data='menu')],
        [InlineKeyboardButton('Оплата', callback_data='payment')]
        ]
    reply_markup = InlineKeyboardMarkup(product_keyboard)

    message = dedent(f'''
    {product['name']}

    {product['price']} руб

    {product['description']}
    ''')
    
    context.bot.send_photo(chat_id=chat_id, photo=image,
                   caption=message, reply_markup=reply_markup)
    context.bot.delete_message(chat_id=chat_id, message_id=query.message.message_id)

    return 'HANDLE_DESCRIPTION'


def handle_description(update, context):
    check_access_token()
    query = update.callback_query
    chat_id = query.message.chat_id
    product = products[int(query.data)]

    add_product_to_cart(token=moltin_token,
                        product_id=product['id'],
                        quantity=1,
                        chat_id=chat_id)
    message = f'Добавлена {product["name"]} в корзину'
    context.bot.answer_callback_query(callback_query_id=query.id, text=message)

    return 'HANDLE_DESCRIPTION'


def handle_cart(update, context):
    check_access_token()
    query = update.callback_query
    chat_id = query.message.chat_id

    if 'remove' in query.data:
        product_id = query.data.split(',')[1]
        remove_cart_items(token=moltin_token, 
                          product_id=product_id, 
                          chat_id=chat_id)

    message = ''
    cart_keyboard = []
    cart, total_amount = get_cart_items(token=moltin_token, 
                                        chat_id=chat_id)

    for product in cart:
        cart_keyboard.append([InlineKeyboardButton(
            f"Убрать из корзины {product['name']}", 
            callback_data=f"remove,{product['id']}")])

        product_output = dedent(f'''
            Пицца {product['name']}
            {product['description']}
            По цене {product['price']} руб

            В заказе {product['quantity']} за {product['amount']} руб
            ''')
        message += product_output

    cart_keyboard.append([InlineKeyboardButton('Меню', callback_data='menu')])
    cart_keyboard.append([InlineKeyboardButton('Оплата', callback_data='payment')])
    reply_markup = InlineKeyboardMarkup(cart_keyboard)
    message += f'\nВсего к оплате: {total_amount} руб'

    context.bot.send_message(chat_id=chat_id, 
                     text=message, 
                     reply_markup=reply_markup)
    context.bot.delete_message(chat_id=query.message.chat_id, 
                       message_id=query.message.message_id)

    return 'HANDLE_CART'


def handle_waiting(update, context):
    global pizzerias
    query = update.callback_query
    context.bot.send_message(chat_id=query.message.chat_id, 
                text='Пожалуйста, напишите адрес текстом или пришлите локацию')
    pizzerias = get_all_entries(moltin_token)

    return 'HANDLE_LOCATION'


def handle_location(update, context):
    check_access_token()
    chat_id = update.message.chat_id

    if update.message.text:
        try:
            lon, lat = fetch_coordinates(update.message.text)
        except IndexError:
            context.bot.send_message(chat_id=chat_id, 
                        text='К сожалению не удалось определить локацию. Попробуйте еще раз')
            return 'HANDLE_LOCATION'

    else:
        lat = update.message.location.latitude
        lon = update.message.location.longitude
    
    message = get_min_distance(lon, lat, pizzerias)
    update.message.reply_text(message)

    return 'HANDLE_LOCATION'


def handle_users_reply(update, context):
    global menu_page_number
    query = update.callback_query
    db = get_database_connection()

    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif query:
        user_reply = query.data
        chat_id = query.message.chat_id
    else:
        return

    if user_reply == '/start':
        user_state = 'START'
    elif user_reply == 'cart':
        user_state = 'HANDLE_CART'
    elif user_reply == 'payment':
        user_state = 'HANDLE_WAITING'
    elif user_reply == 'menu':
        user_state = 'START'
    elif user_reply == 'next':
        user_state = 'START'
        menu_page_number += 1
    elif user_reply == 'prev':
        user_state = 'START'
        menu_page_number -= 1
    else:
        user_state = db.get(chat_id).decode("utf-8")

    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_CART': handle_cart,
        'HANDLE_WAITING': handle_waiting,
        'HANDLE_LOCATION': handle_location,
    }

    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(update, context)
        db.set(chat_id, next_state)
    except Exception as err:
        logging.exception(err)


def get_menu_keyboard(products):
    global menu_page_number
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


def fill_products_information(moltin_products_info):
    global products
    check_access_token()
    for product in moltin_products_info:
        products.append({
                'name': product['name'],
                'id': product['id'],
                'description': product['description'],
                'price': product['meta']['display_price']['with_tax']['formatted'],
                'image_id': product['relationships']['main_image']['data']['id']
            })


def get_product_by_id(product_id):
    global products
    for count, product in enumerate(products):
        if product_id == product['id']:
            return product, count
    
    return None



def get_database_connection():
    global _database
    if _database is None:
        database_password = env("DATABASE_PASSWORD")
        database_host = env("DATABASE_HOST")
        database_port = env("DATABASE_PORT")

        _database = redis.Redis(host=database_host,
                                port=database_port,
                                password=database_password)
    return _database


def check_access_token():
    global moltin_token
    global moltin_token_expires
    curent_time = time.time()

    if curent_time >= moltin_token_expires:
        moltin_token, moltin_token_expires = get_access_token()


if __name__ == '__main__':
    token = env("TELEGRAM_TOKEN")
    logging.basicConfig(format="%(process)d %(levelname)s %(message)s",
                        level=logging.WARNING)

    updater = Updater(token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.location, handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.location, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))

    updater.start_polling()