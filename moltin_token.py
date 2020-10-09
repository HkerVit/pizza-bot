from environs import Env
import time
import json
import requests

env = Env()
env.read_env()

client_id = env('MOLTIN_CLIENT_ID')
client_secret = env('MOLTIN_CLIENT_SECRET_TOKEN')


def get_access_token():
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }

    url = 'https://api.moltin.com/oauth/access_token'

    response = requests.post(url, data=data)
    response.raise_for_status()
    access_response = response.json()

    return access_response['access_token'], access_response['expires']

