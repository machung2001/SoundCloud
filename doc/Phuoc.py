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


def get_id_from_collection(url, client_id, result_limit):
    results = []
    full = False
    while True:
        response = requests.get(url)
        if not response.ok:
            print(f"Failed {response.url}")
            continue
        print(f"Hit {response.url}")
        try:
            json_data = response.json()
            collections = json_data['collection']
            if not collections:
                break
            for collection in collections:
                if len(results) < result_limit:
                    results.append(collection['id'])
                else:
                    full = True
                    break
            if full or json_data['next_href'] is None:
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
    item_ids = get_id_from_collection(url, client_id, result_limit)
    if sub_url:
        item_ids.extend(get_id_from_collection(sub_url, client_id, result_limit))
    for item_id in item_ids:
        results.append(func(item_id, client_id))
    return results


def extract_playlist_generals(playlist_id, client_id):
    url = f'https://api-v2.soundcloud.com/playlists/{playlist_id}?client_id={client_id}&limit=9&linked_partitioning=1'
    while True:
        time.sleep(1)
        response = requests.get(url)
        if not response.ok:
            print(f"Failed {response.url}")
            continue
        break

    print(f"Hit {response.url}")
    generals_data = response.json()
    generals_data['user'] = generals_data['user']['id']
    print(generals_data['user'])
    tracks_list = []
    for track in generals_data['tracks']:
        tracks_list.append(track['id'])
    generals_data['tracks'] = tracks_list
    return generals_data


def playlist_info(playlist_id, client_id):
    reposters_url = f'https://api-v2.soundcloud.com/playlists/{playlist_id}/reposters?client_id={client_id}&limit=9&linked_partitioning=1'
    likers_url = f'https://api-v2.soundcloud.com/playlists/{playlist_id}/likers?client_id={client_id}&limit=9&linked_partitioning=1'
    generals_data = extract_playlist_generals(playlist_id, client_id)
    generals_data['reposters'] = get_id_from_collection(reposters_url, client_id, 100)
    generals_data['likers'] = get_id_from_collection(likers_url, client_id, 100)

def get_featured_tracks(client_id, result_limit=50):
    url = f'https://api-v2.soundcloud.com/featured_tracks/top/all-music?linked_partitioning=1&client_id={client_id}&limit=100'
    featured_tracks = get_id_from_collection(url, client_id, result_limit)
    return featured_tracks


def get_featured_tracks(client_id, result_limit=50):
    results = []
    url = f'https://api-v2.soundcloud.com/featured_tracks/top/all-music?linked_partitioning=1&client_id={client_id}&limit=100'
    featured_tracks = get_id_from_collection(url, client_id, result_limit)
    for track in featured_tracks:
        results.append(track_info(track, client_id))
    return featured_tracks


def main():
    client_id = 'qgbUmYdRbdAL2R1aLbVCgwzC7mvh8VKv'
    query = 'imagine dragons'
    api_result_limit = 100
    get_query_item(QueryType.PLAYLISTS, query, client_id, api_result_limit, 1000)
    ###################
    client_id = 'nGKlrpy2IotLQ0QGwBOmIgSFayis6H4e'
    playlist_id = '9801343'
    playlist_info(playlist_id, client_id)

main()
