import json
from enum import Enum

import requests
import csv

#####################
# testing variable, print this to see how many requests ha been made
TOTAL_REQ = 0


def savefile(file_name, json_data):
    keys = set()
    for d in json_data:
        keys.update(d.keys())
    keys = sorted(keys)
    with open(file_name, 'a', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, restval="-", fieldnames=keys, delimiter='\t')
        dict_writer.writeheader()
        dict_writer.writerows(json_data)


# save to some file to debug results
def temp_save(json_data, file):
    with open(file, 'w') as f:
        json.dump(json_data, f, indent=4)


#########################################

def request_url(url, max_req=10):
    global TOTAL_REQ
    req = 0
    while True:
        response = requests.get(url)
        if not response.ok:
            #print(f"Failed {response.url}")
            req += 1
            if req < max_req:
                continue
            else:
                print(f'Aborted url: {response.url}')
                return {}
        break
    #print(f"Hit {response.url}")
    # Testing variable
    TOTAL_REQ += 1
    return response.json()


class QueryType(Enum):
    USERS = 0
    TRACKS = 1
    PLAYLISTS = 2


def get_id_from_collection(url, client_id, result_limit, option=None):
    results = []
    full = False
    while True:
        json_data = request_url(url)
        try:
            collections = json_data['collection']
            if not collections:
                break
            for collection in collections:
                if len(results) < result_limit or result_limit == -1:
                    if option:
                        results.append(collection[option]['id'])
                    else:
                        results.append(collection['id'])
                else:
                    full = True
                    break
            if full or json_data['next_href'] is None:
                break
            url = json_data['next_href'] + f'&client_id={client_id}'
        except KeyError:
            break
    return list(set(results))


def get_query_item(q_type, query, client_id, result_limit):
    results = []
    sub_url = ''
    if q_type == QueryType.USERS:
        url = f'https://api-v2.soundcloud.com/search/users?q={query}&client_id={client_id}&limit=100&linked_partitioning=1 '
        func = user_info
    elif q_type == QueryType.TRACKS:
        url = f'https://api-v2.soundcloud.com/search/tracks?q={query}&client_id={client_id}&limit=100&linked_partitioning=1'
        func = track_info
    elif q_type == QueryType.PLAYLISTS:
        url = f'https://api-v2.soundcloud.com/search/albums?q={query}&client_id={client_id}&limit=100&linked_partitioning=1'
        sub_url = f'https://api-v2.soundcloud.com/search/playlists_without_albums?q={query}&client_id={client_id}&limit=100&linked_partitioning=1'
        func = playlist_info
    else:
        raise Exception("Unsupported type")

    item_ids = get_id_from_collection(url, client_id, result_limit)
    if sub_url:
        item_ids.extend(get_id_from_collection(sub_url, client_id, result_limit))
    for item_id in item_ids:
        item_info = func(item_id, client_id)
        if item_info:
            results.append(item_info)
    return results


def extract_playlist_generals(playlist_id, client_id):
    url = f'https://api-v2.soundcloud.com/playlists/{playlist_id}?client_id={client_id}&limit=100&linked_partitioning=1'
    generals_data = request_url(url)
    if generals_data:
        generals_data['user'] = generals_data['user']['id']
        tracks_list = []
        for track in generals_data['tracks']:
            tracks_list.append(track['id'])
        generals_data['tracks'] = list(set(tracks_list))
    return generals_data


def playlist_info(playlist_id, client_id):
    reposters_url = f'https://api-v2.soundcloud.com/playlists/{playlist_id}/reposters?client_id={client_id}&limit=100&linked_partitioning=1'
    likers_url = f'https://api-v2.soundcloud.com/playlists/{playlist_id}/likers?client_id={client_id}&limit=100&linked_partitioning=1'
    generals_data = extract_playlist_generals(playlist_id, client_id)
    if generals_data:
        generals_data['reposters'] = get_id_from_collection(reposters_url, client_id, 100)
        generals_data['likers'] = get_id_from_collection(likers_url, client_id, 100)
    return generals_data


def get_featured_tracks(client_id, result_limit=50):
    results = []
    url = f'https://api-v2.soundcloud.com/featured_tracks/top/all-music?linked_partitioning=1&client_id={client_id}&limit=100'
    featured_tracks = set(get_id_from_collection(url, client_id, result_limit))
    for track in featured_tracks:
        ti = track_info(track, client_id)
        if ti:
            results.append(ti)
    return results


def extract_charts_data(url, client_id):
    results = get_id_from_collection(url, client_id, -1, 'track')
    return results


def get_charts(client_id):
    kind_options = ['trending', 'top']
    genre_options = [
        'soundcloud:genres:all-music',
        'soundcloud:genres:all-audio',
        'soundcloud:genres:alternativerock',
        'soundcloud:genres:ambient',
        'soundcloud:genres:classical',
        'soundcloud:genres:country',
        'soundcloud:genres:danceedm',
        'soundcloud:genres:dancehall',
        'soundcloud:genres:deephouse',
        'soundcloud:genres:disco',
        'soundcloud:genres:drumbass',
        'soundcloud:genres:dubstep',
        'soundcloud:genres:electronic',
        'soundcloud:genres:folksingersongwriter',
        'soundcloud:genres:hiphoprap',
        'soundcloud:genres:house',
        'soundcloud:genres:indie',
        'soundcloud:genres:jazzblues',
        'soundcloud:genres:latin',
        'soundcloud:genres:metal',
        'soundcloud:genres:piano',
        'soundcloud:genres:pop',
        'soundcloud:genres:rbsoul',
        'soundcloud:genres:reggae',
        'soundcloud:genres:reggaeton',
        'soundcloud:genres:rock',
        'soundcloud:genres:soundtrack',
        'soundcloud:genres:techno',
        'soundcloud:genres:trance',
        'soundcloud:genres:trap',
        'soundcloud:genres:triphop',
        'soundcloud:genres:world',
        'soundcloud:genres:audiobooks',
        'soundcloud:genres:business',
        'soundcloud:genres:comedy',
        'soundcloud:genres:entertainment',
        'soundcloud:genres:learning',
        'soundcloud:genres:newspolitics',
        'soundcloud:genres:religionspirituality',
        'soundcloud:genres:science',
        'soundcloud:genres:sports',
        'soundcloud:genres:storytelling',
        'soundcloud:genres:technology'
    ]
    charts_tracks = []
    results = []
    for kind_option in kind_options:
        for genre_option in genre_options:
            url = f'https://api-v2.soundcloud.com/charts?kind={kind_option}&genre={genre_option}&client_id={client_id}&linked_partitioning=1&limit=100'
            charts_tracks.extend(extract_charts_data(url, client_id))
    charts_tracks = set(charts_tracks)
    for track in charts_tracks:
        ti = track_info(track, client_id)
        if ti:
            results.append(ti)
    return results


def get_discover_id(client_id):
    tracks = []
    playlists = []
    url = f'https://api-v2.soundcloud.com/mixed-selections?client_id={client_id}&limit=100&linked_partitioning=1'
    response = request_url(url)
    if not response:
        return tracks, playlists
    collections = response['collection']
    for collection in collections:
        if 'charts' in collection['urn']:
            for no_id_playlist in collection['items']["collection"]:
                for track in no_id_playlist['tracks']:
                    tracks.append(track['id'])
        elif 'playlist' in collection['urn']:
            for playlist in collection['items']['collection']:
                playlists.append(playlist['id'])
        else:
            raise Exception("Unknown type")
    return list(set(tracks)), list(set(playlists))


def get_discover(client_id):
    tracks, playlists = get_discover_id(client_id)

    track_result = []
    playlist_result = []
    for track_id in tracks:
        ti = track_info(track_id, client_id)
        if ti:
            track_result.append(ti)
    for playlist_id in playlists:
        pi = playlist_info(playlist_id, client_id)
        if pi:
            playlist_result.append(pi)
    return track_result, playlist_result


def extract_track_generals(track_id, client_id):
    url = f'https://api-v2.soundcloud.com/tracks/{track_id}?client_id={client_id}&linked_partitioning=1'
    generals_data = request_url(url)
    if generals_data:
        generals_data['user'] = generals_data['user']['id']
    return generals_data


def track_info(track_id, client_id):
    reposters_url = f'https://api-v2.soundcloud.com/tracks/{track_id}/reposters?client_id={client_id}&limit=100&linked_partitioning=1'
    likers_url = f'https://api-v2.soundcloud.com/tracks/{track_id}/likers?client_id={client_id}&limit=100&linked_partitioning=1'
    related_tracks_url = f'https://api-v2.soundcloud.com/tracks/{track_id}/related?client_id={client_id}&limit=100&linked_partitioning=1'
    album_url = f'https://api-v2.soundcloud.com/tracks/{track_id}/albums?&client_id={client_id}&limit=100&linked_partitioning=1'
    playlists_url = f'https://api-v2.soundcloud.com/tracks/{track_id}/playlists_without_albums?client_id={client_id}&limit=100&linked_partitioning=1'
    comments_url = f'https://api-v2.soundcloud.com/tracks/{track_id}/comments?threaded=0&filter_replies=0&client_id={client_id}&limit=100&linked_partitioning=1'

    generals_data = extract_track_generals(track_id, client_id)
    if generals_data:
        generals_data['reposters'] = get_id_from_collection(reposters_url, client_id, 100)
        generals_data['likers'] = get_id_from_collection(likers_url, client_id, 100)
        generals_data['comments'] = get_id_from_collection(comments_url, client_id, 100, 'user')
        generals_data['related_tracks'] = get_id_from_collection(related_tracks_url, client_id, 100)
        generals_data['album'] = get_id_from_collection(album_url, client_id, 100)
        generals_data['playlists'] = get_id_from_collection(playlists_url, client_id, 100)

        generals_data.pop('publisher_metadata')
        generals_data.pop('media')
        generals_data.pop('visuals')
    return generals_data


def user_info(user_id, client_id):
    general_url = f'https://api-v2.soundcloud.com/users/{user_id}?client_id={client_id}&limit=100&linked_partitioning=1'
    web_profile_url = f'https://api-v2.soundcloud.com/users/soundcloud:users:{user_id}/web-profiles?client_id={client_id}'
    spotlight_url = f'https://api-v2.soundcloud.com/users/{user_id}/spotlight?client_id={client_id}&limit=100&linked_partitioning=1'
    user_tracks_url = f'https://api-v2.soundcloud.com/users/{user_id}/tracks?client_id={client_id}&limit=100&linked_partitioning=1'
    user_top_tracks_url = f'https://api-v2.soundcloud.com/users/{user_id}/toptracks?client_id={client_id}&linked_partitioning=1'
    user_albums_url = f'https://api-v2.soundcloud.com/users/{user_id}/albums?client_id={client_id}&limit=100&linked_partitioning=1'
    user_playlist_without_albums_url = f'https://api-v2.soundcloud.com/users/{user_id}/playlists_without_albums?client_id={client_id}&limit=100&linked_partitioning=1'
    related_artist_url = f'https://api-v2.soundcloud.com/users/{user_id}/relatedartists?client_id={client_id}&limit=100&linked_partitioning=1'
    reposts_url = f'https://api-v2.soundcloud.com/stream/users/{user_id}/reposts?client_id={client_id}&limit=100&linked_partitioning=1'
    likes_url = f'https://api-v2.soundcloud.com/users/{user_id}/likes?client_id={client_id}&limit=100&linked_partitioning=1'
    followings_url = f'https://api-v2.soundcloud.com/users/{user_id}/followings?client_id={client_id}&limit=100&linked_partitioning=1'
    followers_url = f'https://api-v2.soundcloud.com/users/{user_id}/followers?client_id={client_id}&limit=100&linked_partitioning=1'

    generals_data = request_url(general_url)
    web_profile = request_url(web_profile_url)
    if generals_data and web_profile:
        generals_data['web_profile'] = web_profile
        generals_data['spotlight_tracks'] = get_id_from_collection(spotlight_url, client_id, 100)
        generals_data['user_tracks'] = get_id_from_collection(user_tracks_url, client_id, 100)
        generals_data['user_top_tracks'] = get_id_from_collection(user_top_tracks_url, client_id, 100)
        generals_data['user_albums'] = get_id_from_collection(user_albums_url, client_id, 100)
        generals_data['user_playlist_without_albums'] = get_id_from_collection(user_playlist_without_albums_url, client_id,
                                                                               100)
        generals_data['related_artist'] = get_id_from_collection(related_artist_url, client_id, 100)
        generals_data['followings'] = get_id_from_collection(followings_url, client_id, 100)
        generals_data['followers'] = get_id_from_collection(followers_url, client_id, 100)
        generals_data['reposts'] = get_id_from_collection(reposts_url, client_id, 100, 'track')
        generals_data['likes'] = get_id_from_collection(likes_url, client_id, 100, 'track')

        generals_data.pop('creator_subscription')
        generals_data.pop('creator_subscriptions')
        generals_data.pop('visuals')
        generals_data.pop('badges')

        web_profile = generals_data.pop('web_profile', None)
        socials = []
        if web_profile:
            for social in web_profile:
                socials.append(social['url'])
        generals_data['socials'] = socials

    return generals_data


def main():
    client_id = 'qgbUmYdRbdAL2R1aLbVCgwzC7mvh8VKv'

main()
