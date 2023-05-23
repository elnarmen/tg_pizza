import logging
import os
from textwrap import dedent

import redis
from dotenv import load_dotenv
from geopy import distance
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, JobQueue

from moltin_api import get_access_token, add_product_to_cart, remove_product_from_cart
from moltin_api import get_all_products, get_cart_total, get_cart_products, get_product_by_id, get_img_url
from moltin_api import get_all_pizzerias, create_customer_entry, get_customer_entry, get_deliveryman_id
from yandex_api import fetch_coordinates


def get_products_keyboard(update, congext):
    products_descriptions = get_all_products(
        congext.bot_data['client_id'],
        congext.bot_data['client_secret']
    )
    congext.bot_data['products_descriptions'] = products_descriptions
    keyboard = []
    for product in products_descriptions['data']:
        keyboard.append([InlineKeyboardButton(
            product['attributes']['name'],
            callback_data=product['id'])])
    keyboard.append([InlineKeyboardButton('Корзина', callback_data='cart')])
    return InlineKeyboardMarkup(keyboard)


def start(update, context):
    reply_markup = get_products_keyboard(update, context)
    if update.message:
        update.message.reply_text('Выберите продукт:', reply_markup=reply_markup)
    else:
        query = update.callback_query
        query.message.reply_text(
            'Выберите продукт',
            reply_markup=reply_markup
        )
        chat_id = update.effective_chat.id
        context.bot.delete_message(
            chat_id=chat_id,
            message_id=query.message.message_id
        )
    return 'HANDLE_MENU'


def handle_menu(update, context):
    keyboard = [
        [
            InlineKeyboardButton('Положить в корзину', callback_data='add_to_cart'),
            InlineKeyboardButton('Назад', callback_data='back')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query = update.callback_query
    product_id = query['data']
    context.bot_data['product_id'] = product_id
    client_id = context.bot_data.get('client_id')
    client_secret = context.bot_data.get('client_secret')
    selected_product = get_product_by_id(client_id, client_secret, product_id)['data']
    product_price = \
        selected_product['meta']['display_price']['without_tax']['formatted']
    product_image_url = get_img_url(client_id, client_secret, product_id)
    chat_id = update.effective_chat.id

    text = dedent(
        f'''
            {selected_product['attributes']['name']}
            Стоимость: {product_price}

            {selected_product['attributes']['description']}
        '''
    )
    if product_image_url:
        context.bot.send_photo(
            photo=product_image_url,
            chat_id=chat_id,
            caption=text,
            reply_markup=reply_markup
        )
    else:
        context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup
        )

    context.bot.delete_message(
        chat_id=chat_id,
        message_id=query.message.message_id, )

    return 'HANDLE_DESCRIPTION'


def handle_description(update, context):
    query = update.callback_query
    cart_id = update.effective_chat.id
    if query['data'] == 'back':
        start(update, context)
        return 'HANDLE_MENU'
    if query['data'] == 'cart':
        return 'HANDLE_CART'
    add_product_to_cart(
        client_id=context.bot_data['client_id'],
        client_secret=context.bot_data['client_secret'],
        cart_id=cart_id,
        product_id=context.bot_data['product_id'],
        quantity=1
    )
    query.answer()
    return 'HANDLE_DESCRIPTION'


def get_cart_contents(client_id, client_secret, cart_id):
    cart_products = get_cart_products(client_id, client_secret, cart_id)
    cart_display = []
    for product in cart_products['data']:
        total_price = \
            product['meta']['display_price']['with_tax']['value']['formatted']
        cart_display.append(dedent(
            f'''\
                {product['name']}
                {product['description'].strip()}
                {product['quantity']} пицц в корзине на сумму {total_price}
            '''
        ))
    keyboard = [
        [InlineKeyboardButton(f"Убрать из корзины '{product['name']}'", callback_data=product["id"])]
        for product in cart_products['data']
    ]
    keyboard.append([InlineKeyboardButton('В меню', callback_data='/start')])
    if cart_products:
        keyboard.append([InlineKeyboardButton('Оплатить', callback_data='payment')])
        cart_display.append(f'К оплате: {get_cart_total(client_id, client_secret, cart_id)}')
    message_text = '\n\n'.join(cart_display) if cart_products else 'Корзина пуста'
    markup = InlineKeyboardMarkup(keyboard)

    return message_text, markup


def send_order_to_deliveryman(update, context, client_id, client_secret, cart_id, deliveryman_id):
    message_text, _ = get_cart_contents(client_id, client_secret, cart_id)
    context.bot.send_message(
        chat_id=deliveryman_id,
        text=message_text,
    )
    context.bot.delete_message(
        chat_id=cart_id,
        message_id=update.callback_query.message.message_id
    )


def send_cart_contents(update, context, client_id, client_secret, cart_id):
    message_text, reply_markup = get_cart_contents(client_id, client_secret, cart_id)
    context.bot.send_message(
        chat_id=cart_id,
        text=message_text,
        reply_markup=reply_markup
    )
    context.bot.delete_message(
        chat_id=cart_id,
        message_id=update.callback_query.message.message_id
    )


def handle_cart(update, context):
    query = update.callback_query
    client_id = context.bot_data['client_id']
    client_secret = context.bot_data['client_secret']
    cart_id = update.effective_chat.id
    if query['data'] == 'cart':
        send_cart_contents(update, context, client_id, client_secret, cart_id)
    elif query['data'] == 'payment':
        handle_location_waiting(update, context)
        return 'LOCATION_WAITING'
    else:
        remove_product_from_cart(client_id, client_secret, cart_id, query['data'])
        send_cart_contents(update, context, client_id, client_secret, cart_id)
    return 'HANDLE_CART'


def handle_location_waiting(update, context):
    query = update.callback_query

    message_keyboard = [[
        KeyboardButton('Отправить геопозицию', request_location=True)
    ]]
    markup = ReplyKeyboardMarkup(message_keyboard,
                                 one_time_keyboard=True,
                                 resize_keyboard=True)
    if update.message and update.message.location:
        handle_location(update, context)
        return send_delivery_terms(update, context)
    if update.message:
        yandex_api_key = context.bot_data['yandex_api_key']
        coords = fetch_coordinates(yandex_api_key, update.message.text)
        if not coords:
            update.message.reply_text(
                text='Не могу распознать адрес. Пожалуйста, проверьте правильность ввода',
                reply_markup=markup
            )
            return 'LOCATION_WAITING'
        lat, lon = coords
        client_id = context.bot_data['client_id']
        client_secret = context.bot_data['client_secret']
        chat_id = update.effective_chat.id
        context.bot_data['customer_coords'] = coords
        create_customer_entry(client_id, client_secret, chat_id, lat, lon)
        return send_delivery_terms(update, context)
    else:
        query.message.reply_text(
            text='Хорошо, пришлите нам Ваш адрес текстом или геолокацию.',
            reply_markup=markup
        )
        context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=update.callback_query.message.message_id
        )
        return 'LOCATION_WAITING'


def handle_location(update, context):
    lat, lon = update.message.location['latitude'], update.message.location['longitude']
    client_id = context.bot_data['client_id']
    client_secret = context.bot_data['client_secret']
    chat_id = update.effective_chat.id

    context.bot_data['customer_coords'] = lat, lon
    create_customer_entry(client_id, client_secret, chat_id, lat, lon)


def get_distances(distances_to_customer):
    return distances_to_customer['distance']


def min_distance_calculation(update, context):
    client_id = context.bot_data['client_id']
    client_secret = context.bot_data['client_secret']
    customer_coords = context.bot_data['customer_coords']
    all_pizzerias_data = get_all_pizzerias(client_id, client_secret)

    pizzerias_with_distance_to_customer = []
    for pizzeria in all_pizzerias_data:
        pizzeria_coords = pizzeria['lat'], pizzeria['lon']
        pizzerias_with_distance_to_customer.append(
            {
                'address': pizzeria['address'],
                'distance': distance.distance(pizzeria_coords, customer_coords).km,
            }
        )
    return min(pizzerias_with_distance_to_customer, key=get_distances)


def send_delivery_terms(update, context):
    nearest_pizzeria = min_distance_calculation(update, context)
    distance_to_customer = nearest_pizzeria['distance']

    keyboard = [
        [InlineKeyboardButton('Доставка', callback_data='shipping')],
        [InlineKeyboardButton('Самовывоз', callback_data='pickup')]
    ]

    if distance_to_customer <= .5:
        text = dedent(
            f''' 
                Может, заберте пиццу из нашей пиццерии неподалёку? 
                Она всего в {distance_to_customer * 1000} метрах от вас!
                вот её адрес: {nearest_pizzeria['address']}.
                А можем и бесплатно доставить, нам не сложно
            '''
        )
    elif distance_to_customer <= 5:
        text = dedent(
            f'''
                Похоже, придётся ехать до вас на самокате. Доставка будет стоить 100 рублей.
                Доставляем или самовывоз?
                
                Адрес для самовывоза: 
                {nearest_pizzeria['address']}
            '''
        )
    elif distance_to_customer <= 20:
        text = dedent(
            f'''
                Доставка будет стоить 300 рублей. Доставляем или самовывоз?
                
                Адрес для самовывоза: 
                {nearest_pizzeria['address']}
            '''
        )
    else:
        rounded_distance = round(distance_to_customer)
        text = dedent(
            f'''
                Простите, но так далеко мы пиццу не доставим.
                Ближайшая пиццерия аж в {rounded_distance} километрах от вас!
            '''
        )
        del keyboard[0]

    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(text=text, chat_id=update.message.chat_id, reply_markup=reply_markup)
    context.bot_data['nearest_pizzeria'] = nearest_pizzeria
    return 'HANDLE_SHIPPING_METHOD'


def handle_shipping_method(update, context):
    query = update.callback_query
    chat_id = update.effective_chat.id
    client_id = context.bot_data['client_id']
    client_secret = context.bot_data['client_secret']
    if query['data'] == 'pickup':
        query.message.reply_text(
            text=dedent(
                f'''
                    Адрес для самовывоза:
                    {context.bot_data['nearest_pizzeria']['address']}
                '''
            )
        )
        return
    deliveryman_id = get_deliveryman_id(
        client_id,
        client_secret,
        context.bot_data['nearest_pizzeria']['address']
    )
    query.message.reply_text(
        text='Ваш заказ принят. Ожидайте доставки'
    )

    send_order_to_deliveryman(update, context,
                              client_id, client_secret,
                              chat_id, deliveryman_id)

    context.job_queue.run_once(
        write_to_customer,
        3600,
        context=chat_id
    )

def write_to_customer(context):
    text=dedent(
            f'''
                Приятного аппетита! *место для рекламы*
                *сообщение что делать если пицца не пришла*
            '''
        )
    context.bot.send_message(
        context.job.context,
        text=text,
    )


def handle_users_reply(update, context):
    """
    Функция, которая запускается при любом сообщении от пользователя и решает как его обработать.
    Эта функция запускается в ответ на эти действия пользователя:
        * Нажатие на inline-кнопку в боте
        * Отправка сообщения боту
        * Отправка команды боту
    Она получает стейт пользователя из базы данных и запускает соответствующую функцию-обработчик (хэндлер).
    Функция-обработчик возвращает следующее состояние, которое записывается в базу данных.
    Если пользователь только начал пользоваться ботом, Telegram форсит его написать "/start",
    поэтому по этой фразе выставляется стартовое состояние.
    Если пользователь захочет начать общение с ботом заново, он также может воспользоваться этой командой.
    """
    db_connection = context.bot_data['db_connection']
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.effective_chat.id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    elif user_reply == 'cart':
        user_state = 'HANDLE_CART'
    else:
        user_state = db_connection.get(chat_id)
    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_CART': handle_cart,
        'LOCATION_WAITING': handle_location_waiting,
        'DELIVERY_TERMS': send_delivery_terms,
        'HANDLE_SHIPPING_METHOD': handle_shipping_method,
    }

    state_handler = states_functions[user_state]
    next_state = state_handler(update, context)
    if next_state:
        db_connection[chat_id] = next_state


def main():
    load_dotenv()
    updater = Updater(os.getenv('TG_TOKEN'))
    dispatcher = updater.dispatcher

    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    yandex_api_key = os.getenv('YANDEX_GEOCODER_API_KEY')
    redis_host = os.getenv('REDIS_HOST')
    redis_port = os.getenv('REDIS_PORT')
    redis_password = os.getenv('REDIS_PASSWORD')
    redis_connection = redis.Redis(
        host=redis_host,
        port=redis_port,
        db=0,
        password=redis_password,
        decode_responses=True
    )

    dispatcher.bot_data['db_connection'] = redis_connection
    dispatcher.bot_data['client_id'] = client_id
    dispatcher.bot_data['client_secret'] = client_secret
    dispatcher.bot_data['yandex_api_key'] = yandex_api_key

    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply, pass_job_queue=True))
    dispatcher.add_handler(MessageHandler(Filters.location, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
