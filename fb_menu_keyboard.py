import os
import requests
import json

import moltin


def send_menu(recipient_id, token, message='menu'):
    elements = get_menu_keyboard_content(token, message)
    params = {'access_token': os.environ['PAGE_ACCESS_TOKEN']}
    headers = {'Content-Type': 'application/json'}
    request_content = json.dumps({
            'recipient': {
                'id': recipient_id
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
    

def get_menu_keyboard_content(token, message):
    categories = moltin.get_all_categories(token)
    first_page_menu = get_first_page_menu()
    if message == '/start' or message == 'menu':
        front_page_category_id = categories['Главная']
        products = moltin.get_products_by_category_id(token, front_page_category_id)
    elif 'start' in message:
        __, category_id = message.split(',')
        products = moltin.get_products_by_category_id(token, category_id)[:5]

    main_pizza_menu = get_main_pizza_menu(products, token, message)

    if message == '/start' or message == 'menu':
        categories_pizza_menu = get_categories_pizza_menu(categories)
        return first_page_menu + main_pizza_menu + categories_pizza_menu
    
    return first_page_menu + main_pizza_menu


def get_first_page_menu():
    return [{
                'title': 'Меню',
                'image_url': 'https://75e710fa02b8.ngrok.io/get_image?type=1',
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
        if message == 'menu':
            buttons = [{
                    'type': 'postback',
                    'title': 'Добавить в корзину',
                    'payload': 'add_to_cart',
                }]
        else:
            buttons = [{
                    'type': 'postback',
                    'title': 'Добавить в корзину',
                    'payload': 'add_to_cart',
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
            buttons.append({
                'type': 'postback',
                'title': 'Главное меню',
                'payload': 'menu',
            })
            menu.append({
                'title': 'Не нашли нужную пиццу?',
                'image_url': 'https://75e710fa02b8.ngrok.io/get_image?type=2',
                'subtitle': 'Посмотрите пиццу из следующих категорий:',
                'buttons': buttons,
            })
            button_count = 0
            buttons = []

    return menu