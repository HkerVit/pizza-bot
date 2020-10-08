from environs import Env
from telegram import (LabeledPrice)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

env = Env()
env.read_env()


def start_payment(update, context, price):
    query = update.callback_query 
    chat_id = query.message.chat_id
    title = "Пицца"
    description = "Оплата заказа пиццы"
    payload = env('PAYLOAD')
    provider_token = env('PAYMENT_TOKEN')
    start_parameter = f'Payment_{chat_id}'
    currency = "RUB"
    price = price
    prices = [LabeledPrice("Test", price * 100)]

    context.bot.send_invoice(chat_id, title, description, payload,
                             provider_token, start_parameter, currency, prices)


def precheckout_callback(update, context):
    query = update.pre_checkout_query
    if query.invoice_payload != env('PAYLOAD'):
        query.answer(ok=False, error_message="Что-то пошло не так...")
    else:
        query.answer(ok=True)


def successful_payment_callback(update, context):
    keyboard = [[InlineKeyboardButton(f'Продолжить', callback_data='card_confirm')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Спасибо за Вашу оплату!", reply_markup=reply_markup)
    context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
