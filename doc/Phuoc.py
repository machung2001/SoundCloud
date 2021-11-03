import json

import requests


#####################
# Base function
# Function to search for id:
def track_info(TRACK_ID, CLIENT_ID):
    result = {}

    url = f'https://api-v2.soundcloud.com/tracks/{TRACK_ID}?client_id={CLIENT_ID}&limit=100&linked_partitioning=1'

    # TODO
    return result


def playlist_info(PLAYLIST_ID, CLIENT_ID):
    result = {}

    url = f'https://api-v2.soundcloud.com/playlists/{PLAYLIST_ID}?client_id={CLIENT_ID}&limit=100&linked_partitioning=1'

    return result


def user_info(USER_ID, CLIENT_ID):
    result = {}

    url = f'https://api-v2.soundcloud.com/users/{USER_ID}?client_id={CLIENT_ID}&limit=100&linked_partitioning=1'

    return result


def temp_save(json_data, file):
    with open(file, 'w') as f:
        json.dump(json_data, f, indent=4)


#########################################


def get_users_id(YOUR_QUERY, YOUR_CLIENT_ID, QUERY_RESULT_LIMIT, RESULT_LIMIT):
    result = []
    full = False
    url = f'https://api-v2.soundcloud.com/search/users?q={YOUR_QUERY}&client_id={YOUR_CLIENT_ID}&limit={QUERY_RESULT_LIMIT}&linked_partitioning=1'
    
    while True:
        response = requests.get(url)
        if not response.ok:
            continue
        json_data = response.json()
        try:
            collections = json_data['collection']
            for collection in collections:
                if len(result) < RESULT_LIMIT:
                    result.append(collection['id'])
                    print(len(result))
                else:
                    full = True
                    break
            if full:
                break
            url = json_data['next_href'] + f'&client_id={YOUR_CLIENT_ID}'
        except KeyError:
            break
    return result


def get_users(YOUR_QUERY, YOUR_CLIENT_ID, QUERY_RESULT_LIMIT, RESULT_LIMIT):
    users = get_users_id(YOUR_QUERY, YOUR_CLIENT_ID, QUERY_RESULT_LIMIT, RESULT_LIMIT)
    temp = {'id': users}
    temp_save(temp, 'test.json')
    result = []
    for user_id in users:
        result.append(user_info(user_id, YOUR_CLIENT_ID))
    return result


def main():
    client_id = 'qgbUmYdRbdAL2R1aLbVCgwzC7mvh8VKv'
    query = 'imagine dragons'
    query_result_limit = 200
    get_users(query, client_id, query_result_limit, 1000)


main()
