import json
import os

import requests
from dotenv import load_dotenv
from moltin_api import create_product, create_flow, create_flow_field, create_flow_entry, create_inventory
from moltin_api import download_img, create_img_relationship, add_product_price, create_node_relationship
from moltin_api import get_all_pizzerias


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

    menu_data = get_json_data(menu_url)
    print(get_all_pizzerias(client_id, client_secret))


if __name__ == '__main__':
    main()

