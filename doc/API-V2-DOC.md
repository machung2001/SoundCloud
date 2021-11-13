# SoundCloud API (v2) Unofficial Documentation  

=================================================================  


0. Documents progress
- [x] Foreword
- [x] Querying
  - [x] Parameters explaining
  - [x] Anything
  - [x] Users query
  - [x] Playlists query
    - [x] Albums query
    - [x] Playlist without albums query
  - [x] Tracks query
- [x] Get data from ids
  - [x] Users
    - [x] User's Generals 
    - [x] Tracks
    - [x] Featured profile
    - [x] Spotlight
    - [x] Web-profile
    - [x] Likes
    - [x] Related artist
    - [x] Following
    - [x] Top tracks
    - [x] Albums
    - [x] Playlist without albums
    - [x] Reposts
    - [x] Followers
  - [x] Playlists
    - [x] Playlist generals
    - [x] Playlist likers
    - [x] Playlist Reposters
  - [x] Tracks
    - [x] Track's generals 
    - [x] Track's comments
    - [x] Related tracks
    - [x] In albums
    - [x] Reposters
    - [x] Likers
    - [x] In playlist
	
- [x] Generals
  - [x] [Discover](https://soundcloud.com/discover)
  - [x] [Charts](https://soundcloud.com/charts)
  - [x] [Featured](https://soundcloud.com/)
- [ ] Currently playing (?)
- [ ] Format
 
===================================================================

1. [Foreword](#1-foreword)  
2. [API](#2-api)
- [Parameters explaining](#parameters-explaining)
- [Querying](#querying)
  - [Anything](#anything)
  - [Users query](#users-query)
  - [Tracks query](#tracks-query)
  - [Playlists query](#playlists-query)
    - [Albums query](#albums-query)
    - [Playlist without albums query](#playlist-without-albums-query)
- [Get data from ids](#get-data-from-ids)
  - [Users](#users)
    - [User's Generals](#users-generals) 
    - [Featured profile](#featured-profile)
    - [Web profile](#web-profile)
    - [Splotlight](#splotlight)
    - [User's Tracks](#users-tracks)
    - [User's Top tracks](#users-top-tracks)
    - [User's Albums](#users-albums)
    - [User's Playlist without albums](#users-playlist-without-albums)
    - [Related Artist](#related-artist)
    - [Reposts](#reposts)
    - [Likes](#likes)
    - [Following](#following)
    - [Followers](#followers)
  - [Playlists](#playlists)
    - [Playlist's generals](#playlists-generals)
    - [Playlist reposters](#playlist-reposters)
    - [Playlist likers](#playlist-likers)
  - [Tracks](#tracks)
    - [Track's generals](#tracks-generals) 
    - [Related tracks](#related-tracks)
    - [In albums](#in-albums)
    - [In playlist](#in-playlist)
    - [Reposters](#reposters)
    - [Likers](#likers)
    - [Track's comments](#tracks-comments)
- [Generals](#generals)
  - [Discover](#discover)
  - [Featured](#featured)
  - [Charts](#charts)
    
## 1. Foreword
This document is written for Soundcloud v2 API, which has not been officially documented. This version of API is subject to change and may already changed at the time of reading.

Please do be informed that the use of V2 API is against the 'Term of use' of SoundCloud in general and should be used for research purposes only.

At the time written, this API is used for an educational project. 

## 2. API

### Parameters explaining

SoundCloud API provides parameters to work with their API, these parameters will be used by combining, concatenating them into request URL, with a separator between them is the `&` symbol, except for ids, which use `/` or `ids=xxx` in specific cases.

For example:
```
GET 'https://api-v2.soundcloud.com/...?q={YOUR_QUERY}&client_id={YOUR_CLIENT_ID}&.....'
```

For this project, only these parameters are needed:


```
q={YOUR_QUERY}  
```
- `q={YOUR_QUERY}` is the query you want to search for, if you use `tab`, `space`, ... in the query, it must be replaced with appropriate ASCII encode. Though if you use the `requests` library in python, it will do this for you automatically.
```
client_id={YOUR_CLIENT_ID}  
```
- `client_id={YOUR_CLIENT_ID}` contain your user id, this id is unique to each user. There are many ways to get this field, though the easiest one is through your browser:
   - Open the `inspect` option in Chrome, and go to the network tab.
   - Access [SoundCloud website](https://soundcloud.com/) and look for any network transferring in this tab
   - `client_id` will be in most of these transfer `header`, look around a bit and you will find it.
```
limit={QUERY_RESULT_LIMIT}  (optional)
```
- `limit={QUERY_RESULT_LIMIT}`, an optional field, if not specified, the default result return of each query will be 10, add this parameter to the request URL if you want to limit the return results.
```
linked_partitioning=1
```
- `linked_partitioning=1` referring to [SoundCloud pagination](https://developers.soundcloud.com/blog/offset-pagination-deprecated) for more information. Just add it to your initial request.
```
kind={KIND_OPTION}
```
- Use in `charts`, there're 2 available value to this field:
```
KIND_OPTION = [trending, top]
```
```
genre={GENRE_OPTION}
```
- Use in `charts`, there're x available value to this field:
```
GENRE_OPTION = [
	soundcloud:genres:all-music
	soundcloud:genres:all-audio
	soundcloud:genres:alternativerock
	soundcloud:genres:ambient
	soundcloud:genres:classical
	soundcloud:genres:country
	soundcloud:genres:danceedm
	soundcloud:genres:dancehall
	soundcloud:genres:deephouse
	soundcloud:genres:disco
	soundcloud:genres:drumbass
	soundcloud:genres:dubstep
	soundcloud:genres:electronic
	soundcloud:genres:folksingersongwriter
	soundcloud:genres:hiphoprap
	soundcloud:genres:house
	soundcloud:genres:indie
	soundcloud:genres:jazzblues
	soundcloud:genres:latin
	soundcloud:genres:metal
	soundcloud:genres:piano
	soundcloud:genres:pop
	soundcloud:genres:rbsoul
	soundcloud:genres:reggae
	soundcloud:genres:reggaeton
	soundcloud:genres:rock
	soundcloud:genres:soundtrack
	soundcloud:genres:techno
	soundcloud:genres:trance
	soundcloud:genres:trap
	soundcloud:genres:triphop
	soundcloud:genres:world
	soundcloud:genres:audiobooks
	soundcloud:genres:business
	soundcloud:genres:comedy
	soundcloud:genres:entertainment
	soundcloud:genres:learning
	soundcloud:genres:newspolitics
	soundcloud:genres:religionspirituality
	soundcloud:genres:science
	soundcloud:genres:sports
	soundcloud:genres:storytelling
	soundcloud:genres:technology
]
```

### Querying

#### Anything

In this section, we will get the result from a query of any type, this will appear in `Everything` tab, the query is what will be input in the SoundCloud search bar.

Consider the following base URL:
```
https://api-v2.soundcloud.com/search?  
```
Using this base URL with some parameters, we can query for a general search in SoundCloud, which will return items for the query.

For the purpose of this project, api parameter only include a few options, those parameters are:
```
q={YOUR_QUERY}  
client_id={YOUR_CLIENT_ID}  
limit={QUERY_RESULT_LIMIT} (optional) 
linked_partitioning=1
```
With each parameter separated by `&`, we have the full api query request as follows:
```
GET 'https://api-v2.soundcloud.com/search?q={YOUR_QUERY}&client_id={YOUR_CLIENT_ID}&limit={QUERY_RESULT_LIMIT}&linked_partitioning=1'
```
An example of a query search for the term `hello world` may be as follows:
```
GET 'https://api-v2.soundcloud.com/search?q=hello%20world&client_id=xxxxx&limit=20&linked_partitioning=1'
```
This will return the  first `20` result for `hello world` (notice that the `xxx...` are to be replaced with actual `client_id`)

The response from the above request may be represented in `JSON format:
```JSON
{
  "collection": [...],
  "total_results": 10000,
  "next_href": "https://api-v2.soundcloud.com/search?query_urn=soundcloud%3Asearch%3Afa128d89a8d44b76817c180aab6fe0f2&limit=20&offset=20&q=hello%20world",
  "query_urn": "soundcloud:search:fa128d89a8d44b76817c180aab6fe0f2"
}
```

- `collection` is a list of results with the length of the requested `limit` parameter, in this case, `20` item will be returned and stored in this field, we can start extracting this as data.

- `total_result` is the amount of result search query has find
- `next_href` however, is what we must care about, for this contain a link of the next `20` result (or `limit` parameter value).

Parameter `next_href` will be concatenated with `client_id` to produce the next url for api request:
```python
new_url = response['next_href'] + '&client_id=' + YOUR_CLIENT_ID
```

In this case, this url will be:

```
https://api-v2.soundcloud.com/search?query_urn=soundcloud%3Asearch%3Afa128d89a8d44b76817c180aab6fe0f2&limit=20&offset=20&q=hello%20world&client_id=xxxxxxx...
```

This URL will be used to get the next set of results, this process keeps looping until the field `next_href` no longer appears in the response result.

#### Users Query

SoundCloud api also provide users name search

We will use the following base url to query an users name search:
```
https://api-v2.soundcloud.com/search/users?
```
With these parameters:
```
q={YOUR_QUERY}  
client_id={YOUR_CLIENT_ID}  
limit={QUERY_RESULT_LIMIT} (optional)
linked_partitioning=1
```

With each parameter separated by `&`, we have the full api query request as follows:
```
GET 'https://api-v2.soundcloud.com/search/users?q={YOUR_QUERY}&client_id={YOUR_CLIENT_ID}&limit={QUERY_RESULT_LIMIT}&linked_partitioning=1'
```
An example of a query search for the term `escatic` may be as follows:
```
GET 'https://api-v2.soundcloud.com/search/users?q=escatic&client_id=3jXdkVwgGnCwmB9q5e7qkzpaVm4qjQSn&linked_partitioning=1'
```
This will return users which their profile name is `escatic`. In this example, the result is as follow:

```JSON
{
    "collection": [...],
    "total_results": 2,
    "query_urn": "soundcloud:search:cc53cabca6ab4114b4033f2ec6c49c51"
}
```
The field `collection` contain query result, in this case, because there're only `2` users have their profile name `escatic`, this field contain all the results, and there're no `next_href` field. Though if there're more results, this field will appear.


#### Tracks query

Similarly, we can query for tracks.

Base URL:
```
https://api-v2.soundcloud.com/search/tracks?
```
With the following parameters:
```
q={YOUR_QUERY}  
client_id={YOUR_CLIENT_ID}  
limit={QUERY_RESULT_LIMIT}  (optional)
linked_partitioning=1 
```

So the full request URL will be:

```
GET 'https://api-v2.soundcloud.com/search/tracks?q={YOUR_QUERY}&client_id={YOUR_CLIENT_ID}&limit={QUERY_RESULT_LIMIT}&linked_partitioning=1'
```

The return results are similar to the above query searches.

#### Playlists query
There're 2 types of playlists in SoundCloud: `Albums` and `Playlist without ALbums`.
You can toggle between these 2 types of search in [SoundCloud](https://soundcloud.com/) search result filter when using their website.

##### Albums query

These return information about albums fit the search query. These results return when you switch to the `Albums` filter on the website.

Base URL:
```
https://api-v2.soundcloud.com/search/albums?
```

Parameters:
```
q={YOUR_QUERY}  
client_id={YOUR_CLIENT_ID}  
limit={QUERY_RESULT_LIMIT}  (optional)
linked_partitioning=1 
```
To query for an album, you can use the following request URL. 

```
GET 'https://api-v2.soundcloud.com/search/albums?q={YOUR_QUERY}&client_id={YOUR_CLIENT_ID}&limit={QUERY_RESULT_LIMIT}&linked_partitioning=1'
```

##### Playlist without albums query

Playlists are not categorized as albums. These return when you switch to the `Playlists` filter on the website.

Base URL:
```
https://api-v2.soundcloud.com/search/playlists_without_albums?
```

Parameters:
```
q={YOUR_QUERY}  
client_id={YOUR_CLIENT_ID}  
limit={QUERY_RESULT_LIMIT}  (optional)
linked_partitioning=1 
```

Full URL:
```
GET 'https://api-v2.soundcloud.com/search/playlists_without_albums?q={YOUR_QUERY}&client_id={YOUR_CLIENT_ID}&limit={QUERY_RESULT_LIMIT}&linked_partitioning=1'
```
### Get data from ids

#### Users
This section requires the user's id for each specific user.
##### User's Generals
To get general information about a specific user:
```
GET 'https://api-v2.soundcloud.com/users/{USER_ID}?client_id={CLIENT_ID}&limit={RESULT_LIMIT}&linked_partitioning=1'
```
With `USER_ID` is the id of a user. For example, a full URL would be:
```
https://api-v2.soundcloud.com/users/208026368?client_id=YxQYlFPNletSMSZ4b8Svv9FTYgbNbM79&limit=20&linked_partitioning=1
```

To get more information about user, some parameter are required, for example: `/tracks`, `/albums` , ...

##### Featured profile
```
GET 'https://api-v2.soundcloud.com/users/{USER_ID}/featured-profiles?client_id={CLIENT_ID}&limit=10&linked_partitioning=1'
```
##### Web profile
```
GET 'https://api-v2.soundcloud.com/users/soundcloud:users:{USER_ID}/web-profiles?client_id={CLIENT_ID}'
```
##### Splotlight
```
GET 'https://api-v2.soundcloud.com/users/{USER_ID}/spotlight?client_id={CLIENT_ID}&limit={RESULT_LIMIT}&linked_partitioning=1'
```
##### User's Tracks
```
GET 'https://api-v2.soundcloud.com/users/{USER_ID}/tracks?client_id={CLIENT_ID}&limit={RESULT_LIMIT}&linked_partitioning=1'
```
##### User's Top tracks
```
GET 'https://api-v2.soundcloud.com/users/{USER_ID}/toptracks?client_id={CLIENT_ID}&linked_partitioning=1'
```
##### User's Albums
```
GET 'https://api-v2.soundcloud.com/users/{USER_ID}/albums?client_id={CLIENT_ID}&limit={RESULT_LIMIT}&linked_partitioning=1'
```
##### User's Playlist without albums
```
GET 'https://api-v2.soundcloud.com/users/{USER_ID}/playlists_without_albums?client_id={CLIENT_ID}&limit={RESULT_LIMIT}&linked_partitioning=1'
```
##### Related Artist
```
GET 'https://api-v2.soundcloud.com/users/{USER_ID}/relatedartists?client_id={CLIENT_ID}&limit={RESULT_LIMIT}&linked_partitioning=1'
```
##### Reposts
```
GET 'https://api-v2.soundcloud.com/stream/users/{USER_ID}/reposts?client_id={CLIENT_ID}&limit={RESULT_LIMIT}&linked_partitioning=1'
```
##### Likes
```
GET 'https://api-v2.soundcloud.com/users/{USER_ID}/likes?client_id={CLIENT_ID}&limit={RESULT_LIMIT}&linked_partitioning=1'
```
##### Following
```
GET 'https://api-v2.soundcloud.com/users/{USER_ID}/followings?client_id={CLIENT_ID}&limit={RESULT_LIMIT}&linked_partitioning=1'
```
##### Followers
```
GET 'https://api-v2.soundcloud.com/users/{USER_ID}/followers?client_id={CLIENT_ID}&limit={RESULT_LIMIT}&linked_partitioning=1'
```

#### Playlists
This section requires a playlist/album's id for each specific playlist. There seems to be no difference between playlist and albums except for a single boolean field `isAlbums` return from [Playlist generals](#playlists-generals).
Both playlists and albums ids can be used here.

##### Playlist's generals
To get general information about a playlist:
```
GET 'https://api-v2.soundcloud.com/playlists/{PLAYLIST_ID}?client_id={CLIENT_ID}&limit={RESULT_LIMIT}&linked_partitioning=1'
```
##### Playlist reposters
```
GET 'https://api-v2.soundcloud.com/playlists/{PLAYLIST_ID}/reposters?client_id={CLIENT_ID}&limit={RESULT_LIMIT}&linked_partitioning=1'
```
##### Playlist likers
```
GET 'https://api-v2.soundcloud.com/playlists/{PLAYLIST_ID}}/likers?client_id={CLIENT_ID}&limit={RESULT_LIMIT}&linked_partitioning=1'
```
#### Tracks
##### Track's generals 
To get general information about track
```
https://api-v2.soundcloud.com/tracks/{TRACK_ID}?client_id={CLIENT_ID}&linked_partitioning=1
```

##### Related tracks
```
https://api-v2.soundcloud.com/tracks/{TRACK_ID}/related?client_id={CLIENT_ID}&limit={RESULT_LIMIT}&linked_partitioning=1
```
##### In albums
```
https://api-v2.soundcloud.com/tracks/{TRACK_ID}/albums?&client_id={CLIENT_ID}&limit={RESULT_LIMIT}&linked_partitioning=1
```
##### In playlist
```
https://api-v2.soundcloud.com/tracks/{TRACK_ID}/playlists_without_albums?client_id={CLIENT_ID}&limit={RESULT_LIMIT}&linked_partitioning=1
```
##### Reposters
```
https://api-v2.soundcloud.com/tracks/{TRACK_ID}/reposters?client_id={CLIENT_ID}&limit={RESULT_LIMIT}&linked_partitioning=1
```
##### Likers
```
https://api-v2.soundcloud.com/tracks/{TRACK_ID}/likers?client_id={CLIENT_ID}&limit={RESULT_LIMIT}&linked_partitioning=1
```
##### Track's comments
```
https://api-v2.soundcloud.com/tracks/{TRACK_ID}/comments?threaded=0&filter_replies=0&client_id={CLIENT_ID}&limit={RESULT_LIMIT}&linked_partitioning=1
```
### Generals

#### Featured

When accessing [SoundCloud](https://soundcloud.com/), there's usually a list of tracks below the search bar. To get the tracks in this list, you can use:
```
GET 'https://api-v2.soundcloud.com/featured_tracks/top/all-music?linked_partitioning=1&client_id={CLIENT_ID}&limit={RESULT_LIMIT}'
```
This will return a JSON containing a `collection` list that holds all the tracks. There will also be a `next_href` to navigate:
```JSON
{
    "collection": [], 
    "kind": "top", 
    "genre": "all-music", 
    "next_href": "https://api-v2.soundcloud.com/featured_tracks/top/all-music?offset=80&limit=20", 
    "query_urn": None
}
```
Though be careful because the list of `collection` will empty in 2 or 3 requests, the `href_next` field is still present, this is probably a bug from SoundCloud, so a check to validate return contents in `collection is needed.

#### Discover
SoundCloud `Home` tab, or [Discover page](https://soundcloud.com/discover) contain many list of `Tracks` and `Playlists` 
To get data of these lists, we can use the following request URL:
```
GET 'https://api-v2.soundcloud.com/mixed-selections?client_id={CLIENT_ID}&limit=10&linked_partitioning=1'
```

JSON return:
```JSON
{
    "collection": [],
    "next_href": null,
    "query_urn": "soundcloud:selections:29f12c009d6546f8951d180d6943775c"
}
```
Each item in `collection` corresponds to a list on this page.

#### Charts

[SoundCloud charts](https://soundcloud.com/charts/) 's data. 
```
GET 'https://api-v2.soundcloud.com/charts?kind={KIND_OPTION}&genre={GENRE_OPTION}&client_id={CLIENT_ID}&linked_partitioning=1'
```
Example return:
```JSON
{
    "genre": "soundcloud:genres:all-audio",
    "kind": "top",
    "last_updated": "2021-10-28T10:08:01Z",
    "collection": [],
    "query_urn": "soundcloud:charts:a615850a7fd94ee285154f71d73add9f",
    "next_href": "https://api-v2.soundcloud.com/charts?genre=soundcloud%3Agenres%3Aall-audio&query_urn=soundcloud%3Acharts%3Aa615850a7fd94ee285154f71d73add9f&offset=20&kind=top&limit=20"
}
```
We can follow `next_href` to get the next set of results
