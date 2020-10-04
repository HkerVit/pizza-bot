import requests
import json
import time

from moltin_token import get_access_token

token = None
token_time = 0

def create_flow(token):
    headers = {
        'Authorization': f'{token}',
        'Content-Type': 'application/json',
    }

    data = { 
        "data": { 
            "type": "flow", 
            "name": "Customer Address", 
            "slug": "customer-address", 
            "description": "Customer address", 
            "enabled": True
            } 
        }
    url = 'https://api.moltin.com/v2/flows'
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()


def create_flow_fields(token):
    headers = {
        'Authorization': f'{token}',
        'Content-Type': 'application/json',
    }

    data = { 
        "data": { 
            "type": "field", 
            "name": "Latitude", 
            "slug": "latitude", 
            "field_type": "float", 
            "description": "Client latitude", 
            "required": False, 
            "default": 0, 
            "enabled": False, 
            "order": 3, 
            "omit_null": False, 
            "relationships": { 
                "flow": { 
                    "data": { 
                        "type": "flow", 
                        "id": "4dcff197-d8c5-49a2-b6fa-18da5868851a" 
                            } 
                        } 
                    } 
                },
            }
    url = 'https://api.moltin.com/v2/fields'

    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()


def get_all_entries():
    headers = {
        'Authorization': f'Bearer {token}',
    }

    url = 'https://api.moltin.com/v2/flows/pizzeria/entries'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    print(response.json())

    pizzerias = []
    for pizzeria in response.json()['data']:
        pizzerias.append({
            'id': pizzeria['id'],
            'address': pizzeria['address'],
            'alias': pizzeria['alias'],
            'lon': pizzeria['longitude'],
            'lat': pizzeria['latitude'],
            'deliveryman': pizzeria['deliveryman']
        })
    
    return pizzerias


def update_entire(entire_id):
    headers = {
        'Authorization': f'{token}',
        'Content-Type': 'application/json',
    }

    data = { 
        "data": { 
            "id": entire_id, 
            "type": "entry",
            "deliveryman": 709271509,
            } 
        }


    url = f'https://api.moltin.com/v2/flows/pizzeria/entries/{entire_id}'
    response = requests.put(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()
    