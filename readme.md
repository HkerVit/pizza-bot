# Pizza telegram bot

The Telegram bot provides access to the pizza-shop. You can choose a pizza what you want, get a descriptions of chosen pizza with the picture, add the pizza to the cart, remove from the cart, and send the request for the payment. This bot use the api of [Elasticpath](https://www.elasticpath.com/) service (before this service was called Molton).

All CRUD methods worked by API [documentation.elasticpath](https://documentation.elasticpath.com/commerce-cloud/docs/api/index.html).

## Get started

Before you begin, ensure you have met the following requirements:

- Programming language is [Python 3.8.1](https://www.python.org/downloads/release/python-381/).

- All dependencies install from `pip install -r requirements.txt`.

- Telegram API wrapper is [python-telegram-bot V11.1.0](https://github.com/python-telegram-bot/python-telegram-bot/tree/v11.1.0).

You have to create on following resources:

- Online store in [Elasticpath](https://www.elasticpath.com/).

- Online database in [RedisLabs](https://redislabs.com).

- Telegram bot via `@BotFather`

Declare default environment variables in `.env` file:

`MOLTIN_CLIENT_ID` - Elasticpath client ID.

`MOLTIN_CLIENT_SECRET_TOKEN` - Elasticpath client secret token.

`DATABASE_PASSWORD` - Redis database password.

`DATABASE_HOST` - Redis database host.

`DATABASE_PORT` - Redis database port.

`TELEGRAM_TOKEN` - your telegram bot token.

`YANDEX_MAP_KEY` - key for access Yandex map API.

`PAYMENT_TOKEN` - token for access your payment service.

`PAYLOAD` - your secret payload for transfer verification.

## How To Use

Before run it recommended to install virtual environment:

```bash
python3 -m venv env
source env/bin/activate
```

From your command line:

```shell
python pizza_bot.py
```

Usage example:

![screenshot](screenshot/pizza_bot.gif)

This bot was deployed to Heroku. You can find this bot in Telegram by username: `@pizza_super_bot` and try its work. For payment you can use test credit card:

```
1111 1111 1111 1026
12/22 000
```

## Description of files

Python scripts files:

| filename | description |
|----------|-----------|
|pizza_bot.py|Main script that provide interaction with Telegram API and realise logic|
|keyboard.py|Script provides keyboard and messages for different bot callbacks|
|moltin.py|Interaction with moltin online-shop by APY request|
|moltin_token.py|Get the moltin access token and expiration time|
|fetch_coordinates.py|Interaction with Yandex map API and get geo location (latitude, longitude)from text message|
|closest_pizzeria.py|Script calculates closest pizzeria to customer location|
|payment.py|Interact with Payment service and payment processing|
---

## License

You can copy, distribute and modify the software.

## Motivation

This project was created as part of online course for web developer [dvmn.org](https://dvmn.org/modules/).
