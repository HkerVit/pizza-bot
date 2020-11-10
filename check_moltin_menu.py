import redis
import json
from environs import Env

import moltin
from moltin_token import get_token

_database = None

env = Env()
env.read_env()


def get_full_menu(token, db):
    menu = moltin.get_products_list(moltin_token)
    db.set('menu', json.dumps(menu))
    return menu


def get_categories(token, db):
    categories = moltin.get_all_categories(token)
    db.set('categories', json.dumps(categories))
    return categories


def get_products_by_categories(token, db, categories):
    products_by_categories = {}
    for category in categories:
        products = moltin.get_products_by_category_id(token, categories[category])
        products_by_categories[category] = products
    
    db.set('products_by_categories', json.dumps(products_by_categories))


def get_database_connection():
    global _database
    if _database is None:
        database_password = env("DATABASE_PASSWORD")
        database_host = env("DATABASE_HOST")
        database_port = env("DATABASE_PORT")

        _database = redis.Redis(host=database_host,
                                port=database_port,
                                password=database_password)
    return _database


if __name__ == "__main__":
    db = get_database_connection()
    moltin_token, moltin_token_time = get_token()
    menu = get_full_menu(moltin_token, db)
    categories = get_categories(moltin_token, db)
    get_products_by_categories(moltin_token, db, categories)