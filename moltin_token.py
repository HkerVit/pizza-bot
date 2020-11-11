from environs import Env
import time
import requests
import json

env = Env()
env.read_env()

client_id = env('MOLTIN_CLIENT_ID')
client_secret = env('MOLTIN_CLIENT_SECRET_TOKEN')


def get_token(db):
    current_time = time.time()
    moltin_token = db.get('moltin_token_info')

    if moltin_token and current_time <= float(moltin_token['token_time']):
        moltin_token['token'] = json.loads(db.get('moltin_token'))
        return moltin_token['token']

    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }

    url = 'https://api.moltin.com/oauth/access_token'

    response = requests.post(url, data=data)
    response.raise_for_status()
    access_response = response.json()

    moltin_token = {
        'token': access_response['access_token'],
        'token_time': access_response['expires'],
        }

    db.set('moltin_token', json.dumps(moltin_token))

    return access_response['access_token']