import requests
import json


# It is managing of the product in the moltin shop
def get_products_list(token):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    url = 'https://api.moltin.com/v2/products/'

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    products_response = response.json()
    
    products = []
    for product in products_response['data']:
        products.append({
                'name': product['name'],
                'id': product['id'],
                'description': product['description'],
                'price': product['meta']['display_price']['with_tax']['formatted'],
                'image_id': product['relationships']['main_image']['data']['id']
            })

    return products


def get_product_by_id(token, product_id):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    url = f'https://api.moltin.com/v2/products/{product_id}'

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    product = response.json()['data']

    image_id = product['relationships']['main_image']['data']['id'] 
    image_url = get_image_url(token=token, image_id=image_id)

    return {
        'name' : product['name'],
        'description': product['description'],
        'stock': product['meta']['stock']['level'],
        'price': product['meta']['display_price']['with_tax']['formatted'],
        'image_url': image_url
    }


def get_image_url(token, image_id):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    url = f'https://api.moltin.com/v2/files/{image_id}'

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    image = response.json()

    return image['data']['link']['href']


# It is managing of the cart in the moltin shop
def add_product_to_cart(product_id, token, quantity, chat_id):
    product_data = {
        "data": {
            "id": product_id,
            "type": "cart_item",
            "quantity": int(quantity),
            }
        }

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    url = f'https://api.moltin.com/v2/carts/{chat_id}/items'

    response = requests.post(url,
                             headers=headers,
                             data=json.dumps(product_data))
    response.raise_for_status()


def get_cart_items(token, chat_id):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    url = f'https://api.moltin.com/v2/carts/{chat_id}/items'

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    cart = response.json()

    items =[]
    for item in cart['data']:
        items.append({
            'name': item['name'],
            'id': item['id'],
            'description': item['description'],
            'price': item['meta']['display_price']['with_tax']['unit']['formatted'],
            'quantity': item['quantity'],
            'amount': item['meta']['display_price']['with_tax']['value']['formatted'],
        })

    total_amount = cart['meta']['display_price']['with_tax']['amount']

    return {'items': items, 'total_amount': total_amount}


def remove_cart_item(token, chat_id, product_id):
    headers = {
        'Authorization': f'Bearer {token}',
    }
    url = f'https://api.moltin.com/v2/carts/{chat_id}/items/{product_id}'

    response = requests.delete(url, headers=headers)
    response.raise_for_status()


def remove_all_cart_items(token, chat_id):
    headers = {
        'Authorization': f'Bearer {token}',
    }
    url = f'https://api.moltin.com/v2/carts/{chat_id}'
    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    

# It is managing of the user in the moltin shop
def create_customer(token, username, email, password):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    data = { 
        "data": { 
            "type": "customer", 
            "name": username, 
            "email": email, 
            "password": password
            } 
        }
    url = 'https://api.moltin.com/v2/customers'

    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()


def get_customer(token, customer_id):
    headers = {
        'Authorization': token,
    }

    url = f'https://api.moltin.com/v2/customers/{customer_id}'

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()


def get_all_pizzerias(token):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    url = 'https://api.moltin.com/v2/flows/pizzerias/entries'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    return response.json()['data']


def fill_customer_fields(client_id, lat, lon, token):
    headers = {
        'Authorization': f'{token}',
        'Content-Type': 'application/json',
    }

    data = { 
        "data": { 
            "type": "entry", 
            "client-id": client_id,
            "longitude": lon,
            "latitude": lat,
            } 
        }

    url = 'https://api.moltin.com/v2/flows/customer-address/entries'

    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()