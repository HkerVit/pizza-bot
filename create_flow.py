import requests
import json


def create_flow(token):
    headers = {
        'Authorization': f'{token}',
        'Content-Type': 'application/json',
    }

    data = { 
        "data": { 
            "type": "flow", 
            "name": "Addresses", 
            "slug": "addresses", 
            "description": "Pizzeria addresses", 
            "enabled": True
            } 
        }
    url = 'https://api.moltin.com/v2/flows'
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()

    print(response.json())


def create_flow_fields(token):
    headers = {
        'Authorization': f'{token}',
        'Content-Type': 'application/json',
    }

    data = { 
        "data": { 
            "type": "field", 
            "name": "Address", 
            "slug": "address", 
            "field_type": "string", 
            "description": "Pizzeria address", 
            "required": False, 
            "default": "", 
            "enabled": False, 
            "order": 1, 
            "omit_null": False, 
            "relationships": { 
                "flow": { 
                    "data": { 
                        "type": "flow", 
                        "id": "e8e240bd-8c79-4dc8-9a0f-0eb4e14afc88" 
                            } 
                        } 
                    } 
                },
            }
    url = 'https://api.moltin.com/v2/fields'

    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()


def fill_fields(address, token):
    headers = {
        'Authorization': f'{token}',
        'Content-Type': 'application/json',
    }

    data = { 
        "data": { 
            "type": "entry", 
            "address": address['address']['full'],
            "alias": address['alias'],
            "longitude": address['coordinates']['lon'],
            "latitude": address['coordinates']['lat'],
            } 
        }

    url = 'https://api.moltin.com/v2/flows/pizzeria/entries'

    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()
    print(response.json())
