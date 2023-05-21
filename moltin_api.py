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


def create_product(client_id, client_secret, data):
    access_token = get_access_token(client_id, client_secret)
    url = f'https://api.moltin.com/v2/products'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.post(url, headers=headers, json={'data': data})
    response.raise_for_status()


def create_flow(client_id, client_secret, flow_name):
    access_token = get_access_token(client_id, client_secret)

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    json_data = {
        'data': {
            'type': 'flow',
            'name': f'{flow_name.capitalize()}',
            'slug': f'{flow_name.lower()}',
            'description': f'{flow_name.capitalize()} object',
            'enabled': True,
        },
    }
    url = 'https://api.moltin.com/v2/flows'
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()


def create_flow_field(client_id,
                      client_secret,
                      field_name,
                      field_type,
                      flow_id):
    access_token = get_access_token(client_id, client_secret)
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    json_data = {
        'data': {
            'type': 'field',
            'name': field_name.capitalize(),
            'slug': field_name.lower(),
            'field_type': field_type,
            'description': f'{field_name} field',
            'required': False,
            'default': 0,
            'enabled': True,
            'order': 1,
            'omit_null': False,
            'relationships': {
                'flow': {
                    'data': {
                        'type': 'flow',
                        'id': flow_id,
                    },
                },
            },
        },
    }
    url = 'https://api.moltin.com/v2/fields'
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    return response.json()


def create_flow_entry(client_id, client_secret, flow_slug, address, alias, lat, lon):
    access_token = get_access_token(client_id, client_secret)
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    url = f'https://api.moltin.com/v2/flows/{flow_slug}/entries'

    data = {
            'data': {
                'type': 'entry',
                'address': f'{address}',
                'alias': f'{alias}',
                'lat': f'{lat}',
                'lon': f'{lon}'
            }
        }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()


def create_product(client_id, client_secret, name, sku, description):
    access_token = get_access_token(client_id, client_secret)

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    url = 'https://api.moltin.com/pcm/products'

    json_data = {
        'data': {
            'type': 'product',
            'attributes': {
                'name': f'{name}',
                'sku': f'{sku}',
                'slug': f'{sku}',
                'description': f'{description}',
                'status': 'live',
                'commodity_type': 'physical',
            },
        },
    }

    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    return response.json()['data']['id']


def download_img(client_id, client_secret, img_url):
    access_token = get_access_token(client_id, client_secret)

    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    files = {
        'file_location': (None, img_url),
    }
    url = 'https://api.moltin.com/v2/files'

    response = requests.post(url, headers=headers, files=files)
    response.raise_for_status()
    return response.json()['data']['id']


def create_img_relationship(client_id, client_secret, product_id, image_id):
    access_token = get_access_token(client_id, client_secret)

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    url = f'https://api.moltin.com/pcm/products/{product_id}/relationships/main_image'

    json_data = {
          "data": {
              "type": "file",
              "id": f"{image_id}"
            }
        }

    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()


def add_product_price(client_id, client_secret, sku, price):
    access_token = get_access_token(client_id, client_secret)

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    url = 'https://api.moltin.com/pcm/pricebooks/11e06d2c-16f8-433a-9f86-7ba4ac9b3f36/prices'

    json_data = {
        "data": {
            "type": "product-price",
            "attributes": {
                "sku": f"{sku}",
                "currencies": {
                    "USD": {
                        "amount": price,
                        'includes_tax': False
                    }
                }
            }
        }
    }

    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()


def create_node_relationship(client_id, client_secret, product_id):
    access_token = get_access_token(client_id, client_secret)

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    json_data = {
        "data": [
            {
                "type": "product",
                "id": product_id
            }
        ]
    }

    url = 'https://api.moltin.com/pcm/hierarchies/3f0646e0-6e22-420f-a55f-571ced0feb65/nodes/686db177-9123-41d6-a22a-ab6bee608b6c/relationships/products'
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()


def create_inventory(client_id, client_secret, product_id):
    access_token = get_access_token(client_id, client_secret)

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    json_data = {
        "data": {
            "quantity": 100
        }
    }
    url = f'https://api.moltin.com/v2/inventories/{product_id}'
    response = requests.post(url, headers=headers, json=json_data)
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


def get_img_id(client_id, client_secret, prod_id):
    access_token = get_access_token(client_id, client_secret)
    url = f'https://api.moltin.com/pcm/products/{prod_id}/relationships/main_image'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']['id']


def get_img_url(client_id, client_secret, prod_id):
    access_token = get_access_token(client_id, client_secret)

    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    img_id = get_img_id(client_id, client_secret, prod_id)
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
    return response.json()


# def create_customer(client_id, client_secret, user_name, user_email):
#     access_token = get_access_token(client_id, client_secret)
#     headers = {
#         'Authorization': f'Bearer {access_token}',
#         'Content-Type': 'application/json',
#     }
#
#     data = {
#         'data': {
#             'type': 'customer',
#             'name': user_name,
#             'email': user_email,
#         },
#     }
#     response = requests.post(
#         'https://api.moltin.com/v2/customers',
#         headers=headers,
#         json=data
#     )
#     response.raise_for_status()
