import json
import os

import requests
from dotenv import load_dotenv
from moltin_api import create_product, create_flow, create_flow_field, create_pizzeria_entry, create_inventory
from moltin_api import download_img, create_img_relationship, add_product_price, create_node_relationship
from moltin_api import get_all_pizzerias, change


addresses_url = 'https://dvmn.org/media/filer_public/90/90/9090ecbf-249f-42c7-8635-a96985268b88/addresses.json'

menu_url = 'https://dvmn.org/media/filer_public/a2/5a/a25a7cbd-541c-4caf-9bf9-70dcdf4a592e/menu.json'


def get_json_data(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def main():
    load_dotenv()
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')

    # create_flow_field(client_id, client_secret, 'chat_id', 'integer', '7b5738ca-f926-42ee-9243-85e700fb1f29')
    # create_flow_field(client_id, client_secret, 'address', 'string', '7b5738ca-f926-42ee-9243-85e700fb1f29')
    # create_flow_field(client_id, client_secret, 'alias', 'string', '7b5738ca-f926-42ee-9243-85e700fb1f29')
    # create_flow_field(client_id, client_secret, 'lat', 'string', '7b5738ca-f926-42ee-9243-85e700fb1f29')
    # create_flow_field(client_id, client_secret, 'lon', 'string', '7b5738ca-f926-42ee-9243-85e700fb1f29')
    pizzerias_data = get_json_data(addresses_url)

    # for pizzeria in pizzerias_data:
    #     address = pizzeria['address']['full']
    #     alias = pizzeria['alias']
    #     chat_id = 363285509
    #     lat = pizzeria['coordinates']['lat']
    #     lon = pizzeria['coordinates']['lon']
    #     create_pizzeria_entry(client_id, client_secret, chat_id, address, alias, lat, lon)
    for entry in get_all_pizzerias(client_id, client_secret)['data']:
        id = entry['id']
        print(change(client_id, client_secret, id))


if __name__ == '__main__':
    main()

