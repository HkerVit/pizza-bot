import json
import requests

from environs import Env

import moltin

env = Env()
env.read_env()


def send_remove_from_cart_message(sender_id, message, token, db):
    user = f'fb_{sender_id}'
    __, item_id = message.split(',')
    moltin.remove_cart_item(token, user, item_id)
    params = {'access_token': env('PAGE_ACCESS_TOKEN')}
    headers = {'Content-Type': 'application/json'}
    text = f'Убрана из корзины'
    request_content = json.dumps({
        "recipient": {
            "id": sender_id
        },
        "message": {
            "text": text
        }
    })
    url = 'https://graph.facebook.com/v2.6/me/messages'
    response = requests.post(url, params=params, headers=headers, data=request_content)
    response.raise_for_status()