import requests
import json

from environs import Env

import moltin
from check_moltin_menu import get_products_by_categories

env = Env()
env.read_env()


def send_menu(sender_id, token, db, message='menu'):
    user = f'fb_{sender_id}'

    elements = get_menu_keyboard_content(token, message, db, user)
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
    

def get_menu_keyboard_content(token, message, db, user):
    categories = db.get('categories')
    if categories is None:
        categories = moltin.get_all_categories(token)
        db.set('categories', json.dumps(categories))
    else:
        categories = json.loads(db.get('categories'))
    
    products_by_categories = db.get('products_by_categories')
    if products_by_categories is None:
        products_by_categories = get_products_by_categories(token, db, categories)
        db.set('product_by_categories', json.dumps(products_by_categories))
    else:
        products_by_categories = json.loads(db.get('products_by_categories'))

    first_page_menu = get_first_page_menu()

    if message == '/start' or message == 'menu':
        products = products_by_categories['Главная']

    elif 'start' in message:
        __, category = message.split(',')
        products = products_by_categories[category][:4]

    main_pizza_menu = get_main_pizzas_menu(products, token, message)

    if message == '/start' or message == 'menu':
        pizzas_categories_menu = get_pizzas_categories_menu(categories)
        return first_page_menu + main_pizza_menu + pizzas_categories_menu
    
    return first_page_menu + main_pizza_menu


def get_first_page_menu():
    return [{
                'title': 'Меню',
                'image_url': env('MENU_IMAGE'),
                'subtitle': 'Здесь вы можете выбрать один из вариантов',
                'buttons': [
                    {
                        'type': 'postback',
                        'title': 'Корзина',
                        'payload': "cart",
                    },
                    {
                        'type': 'postback',
                        'title': 'Акции',
                        'payload': "event",
                    },
                    {
                        'type': 'postback',
                        'title': 'Сделать заказ',
                        'payload': 'order',
                    },
                ]
            }]


def get_main_pizzas_menu(products, token, message):
    menu = []
    for product in products:
        title = f'{product["name"]} ({product["price"]}р.)'
        description = product['description']
        image_url = moltin.get_image_url(token, product['image_id'])
        if message == '/start' or message == 'menu':
            buttons = [{
                    'type': 'postback',
                    'title': 'Добавить в корзину',
                    'payload': f'add_to_cart,{product["id"]}',
                }]
        else:
            buttons = [{
                    'type': 'postback',
                    'title': 'Добавить в корзину',
                    'payload': f'add_to_cart,{product["id"]}',
                },
                {
                'type': 'postback',
                'title': 'Главное меню',
                'payload': 'menu',
                }]
        menu.append({
            'title': title,
            'image_url': image_url,
            'subtitle': description,
            'buttons': buttons,
            })
    return menu


def get_pizzas_categories_menu(categories):
    button_count = 0
    buttons, menu = [], []
    for category in categories:
        if category == 'Главная':
            continue
        payload = f'start,{category}'
        buttons.append({
            'type': 'postback',
            'title': category,
            'payload': payload,
        })
        button_count += 1
        if button_count == 2:
            menu.append({
                'title': 'Не нашли нужную пиццу?',
                'image_url': env('CATEGORY_IMAGE'),
                'subtitle': 'Посмотрите пиццу из следующих категорий:',
                'buttons': buttons,
            })
            button_count = 0
            buttons = []

    return menu