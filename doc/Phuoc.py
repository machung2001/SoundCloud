import json
import time
from enum import Enum

import requests


#####################
# Base function
# Function to search for id:
def track_info(track_id, client_id):
    result = {}

    url = f'https://api-v2.soundcloud.com/tracks/{track_id}?client_id={client_id}&limit=100&linked_partitioning=1'

    # TODO
    return result


def playlist_info(playlist_id, client_id):
    result = {}

    url = f'https://api-v2.soundcloud.com/playlists/{playlist_id}?client_id={client_id}&limit=100&linked_partitioning=1'

    return result


def user_info(user_id, client_id):
    result = {}

    url = f'https://api-v2.soundcloud.com/users/{user_id}?client_id={client_id}&limit=100&linked_partitioning=1'

    return result


def any_query(generals_id, client_id):
    raise NotImplementedError("General query need more consideration to implement or not")


def temp_save(json_data, file):
    with open(file, 'w') as f:
        json.dump(json_data, f, indent=4)


#########################################

class QueryType(Enum):
    ANYTHING = 0
    USERS = 1
    TRACKS = 2
    PLAYLISTS = 3


def get_query_item_ids(url, result_limit, client_id):
    results = []
    full = False
    while True:
        time.sleep(1)
        response = requests.get(url)
        if not response.ok:
            print(f"Failed {response.url}")
            continue
        print(f"Hit {response.url}")
        json_data = response.json()
        try:
            collections = json_data['collection']
            for collection in collections:
                if len(results) < result_limit:
                    results.append(collection['id'])
                else:
                    full = True
                    break
            if full:
                break
            url = json_data['next_href'] + f'&client_id={client_id}'
        except KeyError:
            break
    return results


def get_query_item(q_type, query, client_id, api_result_limit, result_limit):
    results = []
    sub_url = ''
    if q_type == QueryType.USERS:
        url = f'https://api-v2.soundcloud.com/search/users?q={query}&client_id={client_id}&limit={api_result_limit}&linked_partitioning=1'
        func = user_info
    elif q_type == QueryType.TRACKS:
        url = f'https://api-v2.soundcloud.com/search/tracks?q={query}&client_id={client_id}&limit={api_result_limit}&linked_partitioning=1'
        func = track_info
    elif q_type == QueryType.PLAYLISTS:
        url = f'https://api-v2.soundcloud.com/search/albums?q={query}&client_id={client_id}&limit={api_result_limit}&linked_partitioning=1'
        sub_url = f'https://api-v2.soundcloud.com/search/playlists_without_albums?q={query}&client_id={client_id}&limit={api_result_limit}&linked_partitioning=1'
        func = playlist_info
    else:
        url = f'https://api-v2.soundcloud.com/search?q={query}&client_id={client_id}&limit={api_result_limit}&linked_partitioning=1'
        func = any_query

    if q_type == QueryType.PLAYLISTS:
        result_limit //= 2
    item_ids = get_query_item_ids(url, result_limit, client_id)
    if sub_url:
        item_ids.extend(get_query_item_ids(sub_url, result_limit, client_id))

    temp_save({'id': item_ids}, 'test.json')

    for item_id in item_ids:
        results.append(func(item_id, client_id))


def main():
    client_id = 'qgbUmYdRbdAL2R1aLbVCgwzC7mvh8VKv'
    query = 'imagine dragons'
    api_result_limit = 200
    get_query_item(QueryType.PLAYLISTS, query, client_id, api_result_limit, 1000)


main()
