import json
from enum import Enum
import asyncio
import csv
import aiohttp

#####################
# testing variable, print this to see how many requests has been made
TOTAL_REQ = 0


def savefile(file_name, json_data):
    keys = set()
    for d in json_data:
        keys.update(d.keys())
    keys = sorted(keys)
    with open(file_name, 'w', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, restval="-", fieldnames=keys, delimiter='\t')
        dict_writer.writeheader()
        dict_writer.writerows(json_data)


# save to some file to debug results
def temp_save(json_data, file):
    with open(file, 'w') as f:
        json.dump(json_data, f, indent=4)


async def join_list(l):
    values = ','.join([str(i) for i in l])
    return values


#########################################

async def request_url(url, max_req=10):
    global TOTAL_REQ
    req = 0
    async with aiohttp.ClientSession() as session:
        while True:
            async with session.get(url) as response:
                if not response.ok:
                    print(f"Failed {response.url}")
                    req += 1
                    if req < max_req:
                        continue
                    else:
                        print(f'Aborted url: {response.url}')
                        return {}
                #print(f"Hit {response.url}")
                # Testing variable
                TOTAL_REQ += 1
                return await response.json()


class QueryType(Enum):
    USERS = 0
    TRACKS = 1
    PLAYLISTS = 2


async def get_id_from_collection(url, client_id, result_limit, option=None):
    results = []
    full = False
    while True:
        json_data = await request_url(url)
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


async def get_query_item(q_type, query, client_id, result_limit):
    print(f"getting '{q_type.name}' query for {query} keywords")
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

    item_ids = await get_id_from_collection(url, client_id, result_limit)
    if sub_url:
        item_ids.extend(await get_id_from_collection(sub_url, client_id, result_limit))
    # TODO:
    # item_ids = item_ids[:3]
    print(f"Found {len(item_ids)} items for type {q_type.name} with {query} keyword")
    for item_id in item_ids:
        item_info = await func(item_id, client_id)
        if item_info:
            results.append(item_info)
            print(f"Complete {len(results)} / {len(item_ids)} - {q_type.name} - {query}")
    return results


async def extract_playlist_generals(playlist_id, client_id):
    url = f'https://api-v2.soundcloud.com/playlists/{playlist_id}?client_id={client_id}&limit=100&linked_partitioning=1'
    generals_data = await request_url(url)
    if generals_data:
        generals_data['user'] = generals_data['user']['id']
        tracks_list = []
        for track in generals_data['tracks']:
            tracks_list.append(track['id'])
        generals_data['tracks'] = list(set(tracks_list))
    return generals_data


async def playlist_info(playlist_id, client_id):
    reposters_url = f'https://api-v2.soundcloud.com/playlists/{playlist_id}/reposters?client_id={client_id}&limit=100&linked_partitioning=1'
    likers_url = f'https://api-v2.soundcloud.com/playlists/{playlist_id}/likers?client_id={client_id}&limit=100&linked_partitioning=1'
    generals_data = await extract_playlist_generals(playlist_id, client_id)
    if generals_data:
        generals_data['reposters'] = await join_list(await get_id_from_collection(reposters_url, client_id, 100))
        generals_data['likers'] = await join_list(await get_id_from_collection(likers_url, client_id, 100))
        generals_data['tracks'] = await join_list(generals_data['tracks'])
    return generals_data


async def get_featured(client_id, result_limit=50):
    print("get_featured_ran")
    results = []
    url = f'https://api-v2.soundcloud.com/featured_tracks/top/all-music?linked_partitioning=1&client_id={client_id}&limit=100'
    featured_tracks = await get_id_from_collection(url, client_id, result_limit)
    # TODO:
    # featured_tracks = featured_tracks[:2]
    print(f"Found {len(featured_tracks)} featured tracks")
    for track in featured_tracks:
        ti = await track_info(track, client_id)
        if ti:
            results.append(ti)
            print(f"Complete {len(results)} / {len(featured_tracks)} featured tracks")
    return results


async def extract_charts_data(url, client_id):
    results = await get_id_from_collection(url, client_id, -1, 'track')
    return results


async def get_charts(client_id):
    print("get_charts_ran")
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
            charts_tracks.extend(await extract_charts_data(url, client_id))
    charts_tracks = list(set(charts_tracks))
    # TODO:
    # charts_tracks = charts_tracks[:2]
    print(f"Found {len(charts_tracks)} charts tracks")
    for track in charts_tracks:
        ti = await track_info(track, client_id)
        if ti:
            results.append(ti)
            print(f"Complete {len(results)} / {len(charts_tracks)} charts tracks")
    return results


async def get_discover_id(client_id):
    tracks = []
    playlists = []
    url = f'https://api-v2.soundcloud.com/mixed-selections?client_id={client_id}&limit=100&linked_partitioning=1'
    response = await request_url(url)
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


async def get_discover(client_id):
    print("get_discover_ran")
    tracks, playlists = await get_discover_id(client_id)
    # TODO:
    # playlists = playlists[:2]
    # tracks = tracks[:2]
    print(f"Found {len(tracks)} discover tracks")
    print(f"Found {len(playlists)} discover playlist")

    track_result = []
    playlist_result = []
    for track_id in tracks:
        ti = await track_info(track_id, client_id)
        if ti:
            track_result.append(ti)
            print(f"Complete {len(track_result)} / {len(tracks)} discover tracks")
    for playlist_id in playlists:
        pi = await playlist_info(playlist_id, client_id)
        if pi:
            playlist_result.append(pi)
            print(f"Complete {len(playlist_result)} / {len(playlists)} discover playlists ")
    return track_result, playlist_result


async def extract_track_generals(track_id, client_id):
    url = f'https://api-v2.soundcloud.com/tracks/{track_id}?client_id={client_id}&linked_partitioning=1'
    generals_data = await request_url(url)
    if generals_data:
        generals_data['user'] = generals_data['user']['id']
    return generals_data


async def track_info(track_id, client_id):
    reposters_url = f'https://api-v2.soundcloud.com/tracks/{track_id}/reposters?client_id={client_id}&limit=100&linked_partitioning=1'
    likers_url = f'https://api-v2.soundcloud.com/tracks/{track_id}/likers?client_id={client_id}&limit=100&linked_partitioning=1'
    related_tracks_url = f'https://api-v2.soundcloud.com/tracks/{track_id}/related?client_id={client_id}&limit=100&linked_partitioning=1'
    album_url = f'https://api-v2.soundcloud.com/tracks/{track_id}/albums?&client_id={client_id}&limit=100&linked_partitioning=1'
    playlists_url = f'https://api-v2.soundcloud.com/tracks/{track_id}/playlists_without_albums?client_id={client_id}&limit=100&linked_partitioning=1'
    comments_url = f'https://api-v2.soundcloud.com/tracks/{track_id}/comments?threaded=0&filter_replies=0&client_id={client_id}&limit=100&linked_partitioning=1'

    generals_data = await extract_track_generals(track_id, client_id)
    if generals_data:
        generals_data['reposters'] = await join_list(await get_id_from_collection(reposters_url, client_id, 100))
        generals_data['likers'] = await join_list(await get_id_from_collection(likers_url, client_id, 100))
        generals_data['comments'] = await join_list(await get_id_from_collection(comments_url, client_id, 100, 'user'))
        generals_data['related_tracks'] = await join_list(
            await get_id_from_collection(related_tracks_url, client_id, 100))
        generals_data['album'] = await join_list(await get_id_from_collection(album_url, client_id, 100))
        generals_data['playlists'] = await join_list(await get_id_from_collection(playlists_url, client_id, 100))

        generals_data.pop('publisher_metadata')
        generals_data.pop('media')
        generals_data.pop('visuals')
    return generals_data


async def user_info(user_id, client_id):
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

    generals_data = await request_url(general_url)
    if generals_data:
        generals_data['web_profile'] = await request_url(web_profile_url)
        generals_data['spotlight_tracks'] = await join_list(await get_id_from_collection(spotlight_url, client_id, 100))
        generals_data['user_tracks'] = await join_list(await get_id_from_collection(user_tracks_url, client_id, 100))
        generals_data['user_top_tracks'] = await join_list(
            await get_id_from_collection(user_top_tracks_url, client_id, 100))
        generals_data['user_albums'] = await join_list(await get_id_from_collection(user_albums_url, client_id, 100))
        generals_data['user_playlist_without_albums'] = await join_list(
            await get_id_from_collection(user_playlist_without_albums_url,
                                         client_id,
                                         100))
        generals_data['related_artist'] = await join_list(
            await get_id_from_collection(related_artist_url, client_id, 100))
        generals_data['followings'] = await join_list(await get_id_from_collection(followings_url, client_id, 100))
        generals_data['followers'] = await join_list(await get_id_from_collection(followers_url, client_id, 100))
        generals_data['reposts'] = await join_list(await get_id_from_collection(reposts_url, client_id, 100, 'track'))
        generals_data['likes'] = await join_list(await get_id_from_collection(likes_url, client_id, 100, 'track'))

        generals_data.pop('creator_subscription')
        generals_data.pop('creator_subscriptions')
        generals_data.pop('visuals')
        generals_data.pop('badges')

        web_profile = generals_data.pop('web_profile', None)
        socials = []
        if web_profile:
            for social in web_profile:
                socials.append(social['url'])
        generals_data['socials'] = ','.join(socials)

    return generals_data


def extract_data(results):
    tracks = []
    playlists = []
    users = []

    generals_data = results[0]
    query_data = results[1]

    for charts_track in generals_data[0]:
        tracks.append(charts_track)
    for discover_track in generals_data[1][0]:
        tracks.append(discover_track)
    for discover_playlist in generals_data[1][1]:
        playlists.append(discover_playlist)
    for featured_track in generals_data[2]:
        tracks.append(featured_track)

    for query_results in query_data:
        for query_playlist in query_results[0]:
            playlists.append(query_playlist)
        for query_user in query_results[1]:
            users.append(query_user)
        for query_track in query_results[2]:
            tracks.append(query_track)
    tracks = list({track['id']: track for track in tracks}.values())
    playlists = list({playlist['id']: playlist for playlist in playlists}.values())
    users = list({user['id']: user for user in users}.values())
    return tracks, playlists, users


async def main():
    client_id = 'qgbUmYdRbdAL2R1aLbVCgwzC7mvh8VKv'

    keyword_list = ['adele', 'justin', 'adam', 'imagine dragon']
    query_tasks = []
    for keyword in keyword_list:
        tasks = asyncio.gather(
            get_query_item(QueryType.PLAYLISTS, keyword, client_id, 1000),
            get_query_item(QueryType.USERS, keyword, client_id, 1000),
            get_query_item(QueryType.TRACKS, keyword, client_id, 1000),
        )
        query_tasks.append(tasks)
    query_tasks = asyncio.gather(*query_tasks)
    general_tasks = asyncio.gather(
        get_charts(client_id),
        get_discover(client_id),
        get_featured(client_id)
    )
    results = await asyncio.gather(general_tasks, query_tasks)
    tracks, playlists, users = extract_data(results)

    temp_save(tracks, 'tracks.json')
    temp_save(playlists, 'playlists.json')
    temp_save(users, 'users.json')

    savefile('tracks_file.csv', tracks)
    savefile('playlists_file.csv', playlists)
    savefile('users_file.csv', users)


asyncio.get_event_loop().run_until_complete(main())
# await main()
