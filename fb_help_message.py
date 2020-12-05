import requests

from environs import Env

env = Env()


def send_help_message(sender_id, message):
    params = {'access_token': env('PAGE_ACCESS_TOKEN')}
    headers = {'Content-Type': 'application/json'}
    text = f'Невозможно распознать команду {message}. Для начала нажмите старт'
    request_content = {
            'recipient': {
                'id': sender_id
            },
            'message': {
                'attachment': {
                    'type': 'template',
                    'payload': {
                        'template_type': 'button',
                        'text': text,
                        'buttons': [{ 
                            'type': 'postback', 
                            'title': 'start', 
                            'payload': '/start'
                            }] 
                    }
                }
            }
        }
    url = 'https://graph.facebook.com/v2.6/me/messages'
    response = requests.post(url, params=params, headers=headers, json=request_content)
    response.raise_for_status()