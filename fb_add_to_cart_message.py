import json
import requests

from environs import Env

import moltin

env = Env()
env.read_env()


def send_add_to_cart_message(recipient_id, message, token, db):
    user = f'fb_{recipient_id}'
    __, product_id = message.split(',')
    quantity = 1
    moltin.add_product_to_cart(product_id, token, quantity, user)
    products = json.loads(db.get('products'))
    product = next((product for product in products if product['id'] == product_id))
    params = {'access_token': env('PAGE_ACCESS_TOKEN')}
    headers = {'Content-Type': 'application/json'}
    text = f'Пицца {product["name"]} добавлена в корзину'
    request_content = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": text
        }
    })
    url = 'https://graph.facebook.com/v2.6/me/messages'
    response = requests.post(url, params=params, headers=headers, data=request_content)
    response.raise_for_status()