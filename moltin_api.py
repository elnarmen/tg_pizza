import os
import json
import time
from textwrap import dedent

import requests
from dotenv import load_dotenv

MOLTIN_TOKEN_EXPIRES_TIME = 0
MOLTIN_TOKEN = None


def get_access_token(client_id, client_secret):
    global MOLTIN_TOKEN_EXPIRES_TIME
    global MOLTIN_TOKEN

    if time.time() <= MOLTIN_TOKEN_EXPIRES_TIME:
        return MOLTIN_TOKEN

    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    }
    response = requests.post('https://api.moltin.com/oauth/access_token', data=data)
    response.raise_for_status()
    decoded_response = response.json()
    MOLTIN_TOKEN_EXPIRES_TIME = decoded_response.get('expires')
    MOLTIN_TOKEN = decoded_response.get('access_token')
    return MOLTIN_TOKEN


def create_customer_entry(client_id, client_secret, chat_id, lat, lon):
    access_token = get_access_token(client_id, client_secret)
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    url = 'https://api.moltin.com/v2/flows/customer_address/entries'

    data = {
            'data': {
                'type': 'entry',
                'chat_id': chat_id,
                'lat': lat,
                'lon': lon
            }
        }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()


def add_product_to_cart(client_id, client_secret, cart_id, product_id, quantity):
    access_token = get_access_token(client_id, client_secret)
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    data = {
        'data': {
            'id': product_id,
            'type': 'cart_item',
            'quantity': quantity
        }
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()


def remove_product_from_cart(client_id, client_secret, cart_id, product_id):
    access_token = get_access_token(client_id, client_secret)
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items/{product_id}'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_cart_products(client_id, client_secret, cart_id):
    access_token = get_access_token(client_id, client_secret)
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_cart_total(client_id, client_secret, cart_id):
    access_token = get_access_token(client_id, client_secret)
    url = f'https://api.moltin.com/v2/carts/{cart_id}/'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']['meta']['display_price']['with_tax']['formatted']


def get_all_products(client_id, client_secret):
    access_token = get_access_token(client_id, client_secret)
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get('https://api.moltin.com/pcm/products', headers=headers)
    response.raise_for_status()
    return response.json()


def get_product_by_id(client_id, client_secret, product_id):
    access_token = get_access_token(client_id, client_secret)
    url = f'https://api.moltin.com/catalog/products/{product_id}'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_img_url(client_id, client_secret, img_id):
    access_token = get_access_token(client_id, client_secret)

    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    url = f'https://api.moltin.com/v2/files/{img_id}'

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']['link']['href']


def get_all_pizzerias(client_id, client_secret, flow_slug='pizzeria'):
    access_token = get_access_token(client_id, client_secret)
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    url = f'https://api.moltin.com/v2/flows/{flow_slug}/entries'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def get_deliveryman_id(client_id, client_secret, address):
    pizzerias = get_all_pizzerias(client_id, client_secret)
    for pizzeria in pizzerias:
        if address == pizzeria['address']:
            return pizzeria['chat_id']
