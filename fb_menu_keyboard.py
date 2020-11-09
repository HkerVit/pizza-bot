import requests
import json

from environs import Env

import moltin

env = Env()
env.read_env()


def send_menu(sender_id, token, db, message='menu'):
    user = f'fb_{sender_id}'
    if db.get('products') is None:
        products = moltin.get_products_list(token)
        db.set('products', json.dumps(products))
    else:
        products = json.loads(db.get('products'))

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
    if db.get('categories') is None:
        categories = moltin.get_all_categories(token)
        db.set('categories', json.dumps(categories))
    else:
        categories = json.loads(db.get('categories'))

    first_page_menu = get_first_page_menu()

    if message == '/start' or message == 'menu':
        front_page_category_id = categories['Главная']
        user_front_page = f'{user}_front_page'
        if db.get(user_front_page) is None:
            products = moltin.get_products_by_category_id(token, front_page_category_id)
            db.set(user_front_page, json.dumps(products))
        else:
            products = json.loads(db.get(user_front_page))

    elif 'start' in message:
        __, category_id = message.split(',')
        user_product_category = f'{user}_category'
        if db.get(user_product_category) is None:
            products = moltin.get_products_by_category_id(token, category_id)[:5]
            db.set(user_product_category, json.dumps(products))
        else:
            products = json.loads(db.get(user_product_category))

    main_pizza_menu = get_main_pizza_menu(products, token, message)

    if message == '/start' or message == 'menu':
        categories_pizza_menu = get_categories_pizza_menu(categories)
        return first_page_menu + main_pizza_menu + categories_pizza_menu
    
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


def get_main_pizza_menu(products, token, message):
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


def get_categories_pizza_menu(categories):
    button_count = 0
    buttons, menu = [], []
    for category, category_id in categories.items():
        if category == 'Главная':
            continue
        payload = f'start,{category_id}'
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