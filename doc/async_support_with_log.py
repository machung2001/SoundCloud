from enum import Enum
import asyncio
import csv
import aiohttp
from datetime import datetime
import logging

# testing variable, print this to see how many requests has been made
logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.DEBUG)

fileHandler = logging.FileHandler(filename='crawler.log', mode='w')
fileHandler.setFormatter(logFormatter)
fileHandler.setLevel(logging.DEBUG)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
consoleHandler.setLevel(logging.INFO)
rootLogger.addHandler(consoleHandler)


def save_file(file_name, json_data):
    keys = set()
    for d in json_data:
        keys.update(d.keys())
    keys = sorted(keys)
    with open(file_name, 'w', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, restval="-", fieldnames=keys, delimiter='\t')
        dict_writer.writeheader()
        dict_writer.writerows(json_data)


async def join_list(l):
    values = ','.join([str(i) for i in l])
    return values


async def request_url(url, max_req=10):
    req = 0
    try:
        async with aiohttp.ClientSession() as session:
            while True:
                async with session.get(url) as response:
                    if response.status != 200:
                        rootLogger.debug(f"Failed {response.url}")
                        req += 1
                        if req < max_req:
                            continue
                        else:
                            rootLogger.info(f'Aborted url: {response.url}')
                            return {}
                    rootLogger.debug(f"Hit {response.url}")
                    return await response.json()
    except Exception as e:
        rootLogger.error(f'{e}')
        rootLogger.debug(f"REQUEST_URL NEXT ATTEMPT on {url}")
        return await request_url(url, max_req)


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
    rootLogger.debug(f"STARTING... getting all results of type {q_type.name} with query: '{query}'")
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

    tasks = [get_id_from_collection(url, client_id, result_limit)]
    if sub_url:
        tasks.append(get_id_from_collection(sub_url, client_id, result_limit))

    item_ids = await asyncio.gather(*tasks)
    if sub_url:
        item_ids = item_ids[0] + item_ids[1]
    else:
        item_ids = item_ids[0]
    # TODO:
    # item_ids = item_ids[:1]
    rootLogger.info(f"FOUND {len(item_ids)} items for type {q_type.name} with '{query}' keyword")
    for item_id in item_ids:
        result = await func(item_id, client_id)
        if result:
            results.append(result)
            rootLogger.info(f"COMPLETED {len(results)} / {len(item_ids)} - {q_type.name} - '{query}'")

        else:
            rootLogger.info(f"ABORTED 1 query item of type {q_type} with '{query}' keyword")
    # for f in asyncio.as_completed([func(item_id, client_id) for item_id in item_ids]):
    #     result = await f
    #     if result:
    #         results.append(result)
    #         print(f"Completed {len(results)} / {len(item_ids)} - {q_type.name} - '{query}'")
    #     else:
    #         print(f"Aborted 1 query item of type {q_type} with '{query}' keyword")
    rootLogger.info(f"FINISHED: got {len(results)} of type {q_type.name} with query: '{query}'")
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
        sub_info = await asyncio.gather(
            join_list(await get_id_from_collection(reposters_url, client_id, 100)),
            join_list(await get_id_from_collection(likers_url, client_id, 100)),
            join_list(generals_data['tracks'])
        )
        generals_data['reposters'] = sub_info[0]
        generals_data['likers'] = sub_info[1]
        generals_data['tracks'] = sub_info[2]
    return generals_data


async def get_featured(client_id, result_limit=50):
    rootLogger.debug("STARTING... getting SoundCloud's featured items...")
    results = []
    url = f'https://api-v2.soundcloud.com/featured_tracks/top/all-music?linked_partitioning=1&client_id={client_id}&limit=100'
    featured_tracks = await get_id_from_collection(url, client_id, result_limit)
    # TODO:
    # featured_tracks = featured_tracks[:1]
    rootLogger.info(f"FOUND {len(featured_tracks)} featured tracks")

    for track_id in featured_tracks:
        ti = await track_info(track_id, client_id)
        if ti:
            results.append(ti)
            rootLogger.info(f"COMPLETED {len(results)} / {len(featured_tracks)} featured tracks")
        else:
            rootLogger.info(f'ABORTED 1 featured track')

    # for f in asyncio.as_completed([track_info(track_id, client_id) for track_id in featured_tracks]):
    #     ti = await f
    #     if ti:
    #         results.append(ti)
    #         print(f"Completed {len(results)} / {len(featured_tracks)} featured tracks")
    #     else:
    #         print(f"Aborted 1 featured track")
    rootLogger.info(f"FINISHED got {len(results)} featured tracks")
    return results


async def extract_charts_data(url, client_id):
    results = await get_id_from_collection(url, client_id, -1, 'track')
    return results


async def get_charts(client_id):
    rootLogger.debug("STARTING... get SoundCloud's charts items...")
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
    # tasks = []
    for kind_option in kind_options:
        for genre_option in genre_options:
            url = f'https://api-v2.soundcloud.com/charts?kind={kind_option}&genre={genre_option}&client_id={client_id}&linked_partitioning=1&limit=100'
            charts_tracks.extend(await extract_charts_data(url, client_id))

    # for kind_option in kind_options:
    #     for genre_option in genre_options:
    #         url = f'https://api-v2.soundcloud.com/charts?kind={kind_option}&genre={genre_option}&client_id={client_id}&linked_partitioning=1&limit=100'
    #         tasks.append(extract_charts_data(url, client_id))
    # for task in asyncio.as_completed(tasks):
    #     charts_tracks.extend(await task)
    charts_tracks = list(set(charts_tracks))
    # TODO:
    # charts_tracks = charts_tracks[:1]
    rootLogger.info(f"FOUND {len(charts_tracks)} charts tracks")

    for track_id in charts_tracks:
        ti = await track_info(track_id, client_id)
        if ti:
            results.append(ti)
            rootLogger.info(f"COMPLETED {len(results)} / {len(charts_tracks)} charts tracks")
        else:
            rootLogger.info(f"COMPLETED 1 charts track")

    # for f in asyncio.as_completed([track_info(track_id, client_id) for track_id in charts_tracks]):
    #     ti = await f
    #     if ti:
    #         results.append(ti)
    #         print(f"Completed {len(results)} / {len(charts_tracks)} charts tracks")
    #     else:
    #         print(f"Aborted 1 charts track")
    rootLogger.info(f"FINISHED got {len(results)} charts tracks")
    return results


async def get_discover_id(client_id):
    rootLogger.debug(f"STARTING... getting discover tracks and playlists")
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


async def get_discover_tracks(tracks, client_id, track_results):
    for track_id in tracks:
        ti = await track_info(track_id, client_id)
        if ti:
            track_results.append(ti)
            rootLogger.info(f"COMPLETED {len(track_results)} / {len(tracks)} discover tracks")
        else:
            rootLogger.info(f"ABORTED 1 discover track")
    rootLogger.info(f"FINISHED got {len(track_results)} discover tracks")

    # for f in asyncio.as_completed([track_info(track_id, client_id) for track_id in tracks]):
    #     ti = await f
    #     if ti:
    #         track_results.append(ti)
    #         print(f"Completed {len(track_results)} / {len(tracks)} discover tracks")
    #     else:
    #         print(f"Aborted 1 discover track")


async def get_discover_playlists(playlists, client_id, playlist_results):
    for playlist_id in playlists:
        pi = await playlist_info(playlist_id, client_id)
        if pi:
            playlist_results.append(pi)
            rootLogger.info(f"COMPLETED {len(playlist_results)} / {len(playlists)} discover playlist")
        else:
            rootLogger.info(f"ABORTED 1 discover playlist")
    rootLogger.info(f"FINISHED got {len(playlist_results)} discover playlists")

    # for f in asyncio.as_completed([playlist_info(playlist_id, client_id) for playlist_id in playlists]):
    #     pi = await f
    #     if pi:
    #         playlist_results.append(pi)
    #         print(f"Completed {len(playlist_results)} / {len(playlists)} discover playlist")
    #     else:
    #         print(f"Aborted 1 discover playlist")


async def get_discover(client_id):
    tracks, playlists = await get_discover_id(client_id)
    # TODO:
    playlists = playlists[:10]
    tracks = tracks[:10]
    rootLogger.info(f"FOUND {len(tracks)} discover tracks")
    rootLogger.info(f"FOUND {len(playlists)} discover playlist")

    track_results = []
    playlist_results = []

    await asyncio.gather(
        get_discover_tracks(tracks, client_id, track_results),
        get_discover_playlists(playlists, client_id, playlist_results)
    )
    return track_results, playlist_results


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
        sub_info = await asyncio.gather(
            join_list(await get_id_from_collection(reposters_url, client_id, 100)),
            join_list(await get_id_from_collection(likers_url, client_id, 100)),
            join_list(await get_id_from_collection(comments_url, client_id, 100, 'user')),
            join_list(await get_id_from_collection(related_tracks_url, client_id, 100)),
            join_list(await get_id_from_collection(album_url, client_id, 100)),
            join_list(await get_id_from_collection(playlists_url, client_id, 100)),
        )
        generals_data['reposters'] = sub_info[0]
        generals_data['likers'] = sub_info[1]
        generals_data['comments'] = sub_info[2]
        generals_data['related_tracks'] = sub_info[3]
        generals_data['album'] = sub_info[4]
        generals_data['playlists'] = sub_info[5]

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
        sub_info = await asyncio.gather(
            request_url(web_profile_url),
            join_list(await get_id_from_collection(spotlight_url, client_id, 100)),
            join_list(await get_id_from_collection(user_tracks_url, client_id, 100)),
            join_list(await get_id_from_collection(user_top_tracks_url, client_id, 100)),
            join_list(await get_id_from_collection(user_albums_url, client_id, 100)),
            join_list(await get_id_from_collection(user_playlist_without_albums_url, client_id, 100)),
            join_list(await get_id_from_collection(related_artist_url, client_id, 100)),
            join_list(await get_id_from_collection(followings_url, client_id, 100)),
            join_list(await get_id_from_collection(followers_url, client_id, 100)),
            join_list(await get_id_from_collection(reposts_url, client_id, 100, 'track')),
            join_list(await get_id_from_collection(likes_url, client_id, 100, 'track')),
        )
        generals_data['web_profile'] = sub_info[0]
        generals_data['spotlight_tracks'] = sub_info[1]
        generals_data['user_tracks'] = sub_info[2]
        generals_data['user_top_tracks'] = sub_info[3]
        generals_data['user_albums'] = sub_info[4]
        generals_data['user_playlist_without_albums'] = sub_info[5]
        generals_data['related_artist'] = sub_info[6]
        generals_data['followings'] = sub_info[7]
        generals_data['followers'] = sub_info[8]
        generals_data['reposts'] = sub_info[9]
        generals_data['likes'] = sub_info[10]

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
    start_time = datetime.now()
    rootLogger.info('##############################')
    rootLogger.info("CRAWLING DATA BEGIN, DON'T PANIC IF IT LOOK STUCK...")
    rootLogger.info('##############################')

    results = await asyncio.gather(general_tasks, query_tasks)
    tracks, playlists, users = extract_data(results)
    end_time = datetime.now()
    total = end_time - start_time
    total_seconds = int(total.total_seconds())
    hours, remainder = divmod(total_seconds, 60 * 60)
    minutes, seconds = divmod(remainder, 60)
    rootLogger.info('##############################')
    rootLogger.info("DATA CRAWLING COMPLETED")
    rootLogger.info('##############################')
    rootLogger.info('total time: {} hrs {} mins {} secs'.format(hours, minutes, seconds))
    rootLogger.info('result: ')
    rootLogger.info(f'\tTracks: {len(tracks)} items')
    rootLogger.info(f'\tPlaylists: {len(playlists)} items')
    rootLogger.info(f'\tUsers: {len(users)} items')
    rootLogger.info('##############################')
    rootLogger.info("saving data...")
    # temp_save(tracks, 'tracks.json')
    # temp_save(playlists, 'playlists.json')
    # temp_save(users, 'users.json')

    save_file('tracks_file.csv', tracks)
    save_file('playlists_file.csv', playlists)
    save_file('users_file.csv', users)
    rootLogger.info("DONE")


# asyncio.get_event_loop().run_until_complete(main())
# await main()
asyncio.run(main())
