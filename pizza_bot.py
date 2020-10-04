import logging
from textwrap import dedent
import time
import json

import redis
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler
from telegram.ext import (Filters, PreCheckoutQueryHandler)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from environs import Env

from moltin_token import get_access_token
from moltin_bot_function import get_products_list
from moltin_bot_function import add_product_to_cart, remove_cart_items
from moltin_bot_function import get_cart_items, create_customer
from moltin_bot_function import get_image_url
from moltin_bot_function import get_all_entries
from fetch_coordinates import fetch_coordinates
from closest_pizzeria import get_closest_pizzeria
import keyboard
import payment

env = Env()
env.read_env()

_database = None
moltin_token = None
moltin_token_expires = 0
menu_page_number = 0
products = []
cart = []
pizzeria = {}

def start(update, context):
    query = update.callback_query
    if query:
        chat_id = query.message.chat_id
    else:
        chat_id = update.message.chat_id

    check_access_token()
    if time.time() >= moltin_token_expires or len(products) == 0:
        moltin_product_info = get_products_list(token=moltin_token)
        get_all_products(moltin_product_info)

    reply_markup = keyboard.get_menu_keyboard(products, menu_page_number)
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
    product = next((product for product in products if product['id'] == product_id))

    reply_markup, message, image = keyboard.get_product_keyboard_and_text(products, product_id, moltin_token)

    context.bot.send_photo(chat_id=chat_id, photo=image,
                   caption=message, reply_markup=reply_markup)
    context.bot.delete_message(chat_id=chat_id, message_id=query.message.message_id)

    return 'HANDLE_DESCRIPTION'


def handle_description(update, context):
    check_access_token()
    query = update.callback_query
    chat_id = query.message.chat_id
    product_id = query.data

    product = next((product for product in products if product['id'] == product_id))
    add_product_to_cart(token=moltin_token,
                        product_id=product['id'],
                        quantity=1,
                        chat_id=chat_id)
    message = f'Добавлена {product["name"]} в корзину'
    context.bot.answer_callback_query(callback_query_id=query.id, text=message)

    return 'HANDLE_DESCRIPTION'


def handle_cart(update, context):
    global cart
    check_access_token()
    query = update.callback_query
    chat_id = query.message.chat_id

    if 'remove' in query.data:
        product_id = query.data.split(',')[1]
        remove_cart_items(token=moltin_token, 
                          product_id=product_id, 
                          chat_id=chat_id)
    
    reply_markup, message, cart = keyboard.get_cart_keyboard_and_text(moltin_token, chat_id)

    context.bot.send_message(chat_id=chat_id, 
                     text=message, 
                     reply_markup=reply_markup)

    context.bot.delete_message(chat_id=query.message.chat_id, 
                       message_id=query.message.message_id)

    return 'HANDLE_CART'


def handle_waiting(update, context):
    query = update.callback_query
    context.bot.send_message(chat_id=query.message.chat_id, 
                text='Пожалуйста, напишите адрес текстом или пришлите локацию')

    return 'HANDLE_LOCATION'


def handle_location(update, context):
    global pizzeria
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

    reply_markup, message, pizzeria = keyboard.get_location_keyboard_and_text(moltin_token, lon, lat)
    update.message.reply_text(message, reply_markup=reply_markup)

    return 'FINISH'


def handle_delivery(update, context):
    check_access_token()
    query = update.callback_query
    chat_id = query.message.chat_id

    reply_markup, customer_message, delivery_message = keyboard.get_delivery_keyboard_and_text(moltin_token, chat_id, pizzeria, cart)

    query.edit_message_text(customer_message, reply_markup=reply_markup)

    context.bot.send_message(chat_id=pizzeria['deliveryman'], text=delivery_message)
    context.bot.send_location(chat_id=pizzeria['deliveryman'], 
                              latitude=pizzeria['client_lat'], 
                              longitude=pizzeria['client_lon'])
       
    return 'HANDLE_PAYMENT'


def handle_payment(update, context):
    query = update.callback_query 
    chat_id = query.message.chat_id
    amount = cart['total_amount']
    payment.start_payment(update, context, amount) 

    return 'FINISH'
    

def delivery_notification(context):
    message = dedent(f'''
    Приятного аппетита! *место для рекламы*

    *сообщение что делать если пицца не пришла*
    ''')
    job = context.job
    context.bot.send_message(job.context, text=message)


def finish(update, context):
    query = update.callback_query

    if query:
        if query.data == 'close':
            query.edit_message_text('Good bye')
        else:
            chat_id = query.message.chat_id
            lat = pizzeria['lat']
            lon = pizzeria['lon']
            message = dedent(f'''
            Спасибо за то, что выбрали нас.
            Ближайшая к вам пиццерия находится по адресу: 
            {pizzeria['address']}
            ''')
            query.edit_message_text(message)
            context.bot.send_location(chat_id=chat_id, latitude=lat, longitude=lon)

    update.message.reply_text(text='Спасибо за покупку нашей пиццы!')
    context.job_queue.run_once(delivery_notification, 15, context=update.message.chat_id)
    return 'FINISH'


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
    elif user_reply == 'delivery_choice':
        user_state = 'HANDLE_WAITING'
    elif user_reply == 'menu':
        user_state = 'START'
    elif user_reply == 'next':
        user_state = 'START'
        menu_page_number += 1
    elif user_reply == 'prev':
        user_state = 'START'
        menu_page_number -= 1
    elif user_reply == 'delivery':
        user_state = 'HANDLE_DELIVERY'
    else:
        user_state = db.get(chat_id).decode("utf-8")

    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_CART': handle_cart,
        'HANDLE_WAITING': handle_waiting,
        'HANDLE_LOCATION': handle_location,
        'HANDLE_DELIVERY': handle_delivery,
        'HANDLE_PAYMENT': handle_payment,
        'FINISH': finish,
    }

    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(update, context)
        db.set(chat_id, next_state)
    except Exception as err:
        logging.exception(err)


def get_all_products(moltin_products_info):
    global products
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

    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply, pass_job_queue=True))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.location, handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.location, handle_users_reply))
    dispatcher.add_handler(PreCheckoutQueryHandler(payment.precheckout_callback))
    dispatcher.add_handler(MessageHandler(Filters.successful_payment, finish))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))

    updater.start_polling()