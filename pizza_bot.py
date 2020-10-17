import logging
from textwrap import dedent
import time

import redis
from telegram.ext import Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler
from telegram.ext import Filters, PreCheckoutQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from environs import Env

from moltin_token import get_access_token
from fetch_coordinates import fetch_coordinates
import moltin
import keyboard
import payment

env = Env()
env.read_env()

yandex_apikey = env('YANDEX_MAP_KEY')

_database = None
moltin_token = None
moltin_token_expires = 0
products = []
users_carts = {}
users_pizzerias = {}


def start(update, context):
    global products
    check_access_token()
    query = update.callback_query

    if query:
        chat_id = query.message.chat_id
        menu_button = query.data
    else:
        menu_button = update.message.text
        chat_id = update.message.chat_id

    if time.time() >= moltin_token_expires or len(products) == 0:
        products = moltin.get_products_list(token=moltin_token)

    reply_markup = keyboard.get_menu_keyboard(chat_id, products, menu_button)
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
    reply_markup, message, image = keyboard.get_product_reply(products, product_id, moltin_token)

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
    moltin.add_product_to_cart(token=moltin_token,
                               product_id=product['id'],
                               quantity=1,
                               chat_id=chat_id)
    message = f'Добавлена {product["name"]} в корзину'
    context.bot.answer_callback_query(callback_query_id=query.id, text=message)

    return 'HANDLE_DESCRIPTION'


def handle_cart(update, context):
    global users_carts
    check_access_token()
    query = update.callback_query
    chat_id = query.message.chat_id

    if 'remove' in query.data:
        product_id = query.data.split(',')[1]
        moltin.remove_cart_item(token=moltin_token,
                                 product_id=product_id,
                                 chat_id=chat_id)

    reply_markup, message, cart = keyboard.get_cart_reply(moltin_token, chat_id)
    users_carts[chat_id] = cart

    query.edit_message_text(text=message, reply_markup=reply_markup)

    return 'HANDLE_CART'


def handle_waiting(update, context):
    query = update.callback_query
    query.edit_message_text('Пожалуйста, напишите адрес текстом или пришлите локацию')

    return 'HANDLE_LOCATION'


def handle_location(update, context):
    global users_pizzerias
    check_access_token()
    chat_id = update.message.chat_id

    if update.message.text:
        try:
            lon, lat = fetch_coordinates(update.message.text, yandex_apikey)
        except IndexError:
            context.bot.send_message(chat_id=chat_id,
                                     text='К сожалению не удалось определить локацию. Попробуйте еще раз')
            return 'HANDLE_LOCATION'

    else:
        lat = update.message.location.latitude
        lon = update.message.location.longitude

    reply_markup, message, pizzeria, delivery_fee = keyboard.get_location_reply(moltin_token, lon, lat)
    update.message.reply_text(message, reply_markup=reply_markup)
    users_carts[chat_id]['delivery_fee'] = delivery_fee
    users_pizzerias[chat_id] = pizzeria

    return 'HANDLE_DELIVERY'


def handle_delivery(update, context):
    global users_carts
    check_access_token()
    query = update.callback_query
    chat_id = query.message.chat_id
    
    cart = users_carts[chat_id]
    pizzeria = users_pizzerias[chat_id]
    reply_markup, customer_message, cart = keyboard.get_delivery_reply(moltin_token, query, pizzeria, cart)
    query.edit_message_text(customer_message, reply_markup=reply_markup)
    users_carts[chat_id] = cart

    return 'HANDLE_PAYMENT'


def handle_payment(update, context):
    query = update.callback_query
    chat_id = query.message.chat_id

    cart = users_carts[chat_id]
    if query.data == 'cash':
        keyboard = [[InlineKeyboardButton(f'Подтверждаю', callback_data='cash_confirm')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if cart['delivery']:
            message = dedent(f'''
                    К оплате наличными  - {cart["total_amount"]} руб
                    Деньги, пожалуйста, передайте курьеру. Не забудьте взять чек!
                    ''')
            context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)
            return 'HANDLE_DELIVERYMAN'
        else:
            message = dedent(f'''
                    К оплате наличными  - {cart["total_amount"]} руб
                    ''')
            context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)
            return 'FINISH'

    elif query.data == 'card':
        payment.start_payment(update, context, cart['total_amount'])

        if cart['delivery']:
            return 'HANDLE_DELIVERYMAN'
        else:
            return 'FINISH'


def handle_deliveryman(update, context):
    query = update.callback_query
    chat_id = query.message.chat_id

    message = dedent(f'''
            Cпасибо за выбор нашей пиццы!
            Курьер пиццу доставит в течении часа.
            ''')
    query.edit_message_text(message)

    cart = users_carts[chat_id]
    pizzeria = users_pizzerias[chat_id]
    context.bot.send_message(chat_id=pizzeria['deliveryman-chat-id'], text=cart['delivery_message'])
    context.bot.send_location(chat_id=pizzeria['deliveryman-chat-id'],
                              latitude=pizzeria['customer_lat'],
                              longitude=pizzeria['customer_lon'])

    context.job_queue.run_once(delivery_notification, 60, context=query.message.chat_id)

    return 'HANDLE_DELIVERYMAN'


def finish(update, context):
    query = update.callback_query

    if query:
        chat_id = query.message.chat_id
        if query.data == 'close':
            query.edit_message_text('Очень жаль, что не удалось Вам помочь')
    else:
        chat_id = update.message.chat_id

    cart = users_carts[chat_id]
    pizzeria = users_pizzerias[chat_id]
    if not cart['delivery']:
        message = dedent(f'''
           Cпасибо за выбор нашей пиццы!\n
           Ближайшая к вам пиццерия находится по адресу: 
           {pizzeria['address']}\n
           С нетерпением ждем Вас!
           ''')
        if query:
            query.edit_message_text(message)
        else:
            update.message.reply_text(message)
            context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)

        context.bot.send_location(chat_id=chat_id,
                                  latitude=pizzeria['latitude'],
                                  longitude=pizzeria['longitude'])

    return 'FINISH'


def delivery_notification(update, context):
    message = dedent(f'''
    Приятного аппетита! *место для рекламы*\n
    *сообщение что делать если пицца не пришла*
    ''')
    job = context.job
    context.bot.send_message(job.context, text=message)


def handle_users_reply(update, context):
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

    if user_reply == '/start' or user_reply == 'menu':
        user_state = 'START'
    elif 'prev' in user_reply or 'next' in user_reply:
        user_state = 'START'
    elif user_reply == 'cart':
        user_state = 'HANDLE_CART'
    elif user_reply == 'delivery_choice':
        user_state = 'HANDLE_WAITING'
    elif user_reply == 'close':
        user_state = 'FINISH'
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
        'HANDLE_DELIVERYMAN': handle_deliveryman,
        'FINISH': finish,
    }

    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(update, context)
        db.set(chat_id, next_state)
    except Exception as err:
        logging.exception(err)


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
    dispatcher.add_handler(MessageHandler(Filters.successful_payment, payment.successful_payment_callback))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))

    updater.start_polling()
