import json
import requests

from environs import Env

env = Env()
env.read_env()


def send_help_message(recipient_id, message):
    params = {'access_token': env('PAGE_ACCESS_TOKEN')}
    headers = {'Content-Type': 'application/json'}
    text = f'Невозможно распознать команду {message}. Для начала нажмите старт'
    request_content = json.dumps({
            'recipient': {
                'id': recipient_id
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
        })
    url = 'https://graph.facebook.com/v2.6/me/messages'
    response = requests.post(url, params=params, headers=headers, data=request_content)
    response.raise_for_status()