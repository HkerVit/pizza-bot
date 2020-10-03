from io import BytesIO

from slugify import slugify
from PIL import Image


def create_product(pizza, token):
    slug_name = slugify(pizza['name'])
    product_data = {
        "data": {
            "type": "product",
            "name": pizza['name'],
            "slug": slug_name,
            "sku": f'{slug_name}-{pizza["id"]}',
            "manage_stock": False,
            "description": pizza['description'],
            "status": "live",
            "commodity_type": "physical",
            "price": [
                {
                    "amount": pizza['price'],
                    "currency": 'RUB',
                    "includes_tax": True,
                }
            ]
        }
    }

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    url = 'https://api.moltin.com/v2/products'

    response = requests.post(url, headers=headers, data=json.dumps(product_data))
    response.raise_for_status()
    product = response.json()

    return product['data']['id']


def add_image_to_moltin(pizza, token):
    slug_name = slugify(pizza['name'])
    image_url = pizza['product_image']['url']

    response = requests.get(image_url)
    response.raise_for_status()
    img = BytesIO(response.content)

    headers = {
        'Authorization': f'Bearer {token}',
    }

    files = {
         'file': (f'{slug_name}.jpg', img),
         'public': (None, 'true'),
    }

    url = 'https://api.moltin.com/v2/files'
    response = requests.post(url, headers=headers, files=files)
    response.raise_for_status()

    image = response.json()
    
    return image['data']['id']


def add_image_to_product(product_id, image_id, token):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    data = {
        "data": {
            "type": "main_image",
            "id": image_id,
        }
    }

    url = f'https://api.moltin.com/v2/products/{product_id}/relationships/main-image'

    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()