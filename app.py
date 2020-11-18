import logging
import os

from flask import Flask, request, send_file, send_from_directory, url_for
import redis
from environs import Env

import fb_menu_keyboard
import fb_help_message
import fb_cart_keyboard
from fb_add_to_cart_message import send_add_to_cart_message
from fb_remove_from_cart_message import send_remove_from_cart_message
from moltin_token import get_token

app = Flask(__name__, static_url_path='/static')
_database = None

env = Env()
env.read_env()


def handle_start(sender_id, message, db, moltin_token):
    fb_menu_keyboard.send_menu(sender_id, moltin_token, db, message)
    return 'MENU'


def get_help(sender_id, message, moltin_token):
    fb_help_message.send_help_message(sender_id, message)
    return 'START'


def handle_menu(sender_id, message, db, moltin_token):
    if 'add_to_cart' in message:
        send_add_to_cart_message(sender_id, message, moltin_token, db)
    if message == 'cart':
        fb_cart_keyboard.get_cart_keyboard(sender_id, moltin_token)
    return 'MENU'


def handle_cart(sender_id, message, db, moltin_token):
    if 'add_to_cart' in message:
        send_add_to_cart_message(sender_id, message, moltin_token, db)
    if 'remove_from_cart' in message:
        send_remove_from_cart_message(sender_id, message, moltin_token)

    fb_cart_keyboard.get_cart_keyboard(sender_id, moltin_token)
    return 'CART'


def handle_users_reply(sender_id, message_text):
    db = get_database_connection()
    moltin_token = get_token(db)

    states_functions = {
        'START': handle_start,
        'HELP': get_help,
        'MENU': handle_menu,
        'CART': handle_cart,
    }

    user = f'fb_{sender_id}'
    recorded_state = db.get(user)
    if not recorded_state or recorded_state.decode('utf-8') not in states_functions.keys():
        user_state = 'START'
    else:
        if message_text == '/start' or message_text == 'menu':
            user_state = 'START'
        elif 'start' in message_text:
            user_state = 'START'
        elif message_text == 'cart':
            user_state = 'CART'
        else:
            user_state = recorded_state.decode('utf-8')
    
    if user_state is None:
        user_state == 'HELP'
        
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(sender_id, message_text, db, moltin_token)
        db.set(user, next_state)
    except Exception as err:
        logging.exception(err)


@app.route('/', methods=['GET'])
def verify():
    if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.challenge'):
        if not request.args.get('hub.verify_token') == env('VERIFY_TOKEN'):
            return 'Verification token mismatch', 403
        return request.args['hub.challenge'], 200
    
    url = 'qqq'
    return url, 200


@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    if data['object'] == 'page':
        for entry in data['entry']:
            for messaging_event in entry['messaging']:
                if messaging_event.get('message'):
                    sender_id = messaging_event['sender']['id']
                    message = messaging_event['message']['text']
                    handle_users_reply(sender_id, message)
                elif messaging_event.get('postback'):
                    sender_id = messaging_event['sender']['id']
                    payload = messaging_event['postback']['payload']
                    handle_users_reply(sender_id, payload)
    return "ok", 200
    

@app.route('/img/')
def send_img(path):
    return send_from_directory('img', path)


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


if __name__ == '__main__':
    app.run(debug=True)
