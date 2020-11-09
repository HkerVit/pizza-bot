import requests
import json

from environs import Env

import moltin

env = Env()
env.read_env()


def get_cart_keyboard(sender_id, token):
    user = f'fb_{sender_id}'
    cart = moltin.get_cart_items(token, user)

    elements = get_cart_keyboard_content(cart)
    params = {'access_token': env('PAGE_ACCESS_TOKEN')}
    headers = {'Content-Type': 'application/json'}
    request_content = json.dumps({
            'recipient': {
                'id': sender_id
            },
            'message': {
                'attachment': {
                    'type': 'template',
                    'payload': {
                        'template_type': 'generic',
                        'image_aspect_ratio': 'square',
                        'elements': elements
                    }
                }
            }
        })
    url = 'https://graph.facebook.com/v2.6/me/messages'
    response = requests.post(url, params=params, headers=headers, data=request_content)
    response.raise_for_status()


def get_cart_keyboard_content(cart):
    total_amount = cart['total_amount']
    cart_items = cart['items']
    first_cart_page = get_first_cart_page(total_amount)
    items_cart_pages = get_items_cart_pages(cart_items)

    return first_cart_page + items_cart_pages


def get_first_cart_page(total_amount):
    return [{
                'title': 'Корзина',
                'image_url': env('CART_IMAGE'),
                'subtitle': f'Ваш заказ на сумму {total_amount} руб.',
                'buttons': [
                    {
                        'type': 'postback',
                        'title': 'Самовывоз',
                        'payload': "self_delivery",
                    },
                    {
                        'type': 'postback',
                        'title': 'Доставка',
                        'payload': "delivery",
                    },
                    {
                        'type': 'postback',
                        'title': 'К меню',
                        'payload': 'menu',
                    },
                ]
            }]


def get_items_cart_pages(items):
    menu = []
    for item in items:
        title = item['name']
        description = item['description']
        image_url = item['image_url']
        buttons = [{
                    'type': 'postback',
                    'title': 'Добавить еще одну',
                    'payload': f'add_to_cart,{item["product_id"]}',
                },
                {
                    'type': 'postback',
                    'title': 'Убрать из корзины',
                    'payload': f'remove_from_cart,{item["id"]}',
                }]
        menu.append({
            'title': title,
            'image_url': image_url,
            'subtitle': description,
            'buttons': buttons,
            })

    return menu