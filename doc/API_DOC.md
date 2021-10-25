# SoundCloud API (v2) Unofficial Documentation

=================================================================
0. Documents progress
- [x] Foreword
- [ ] Querying
  - [x] Parameters explaining
  - [x] Everything
  - [x] Users
  - [ ] Playlists
    - [ ] Playlist with albums
    - [ ] Playlist without albums
  - [ ] Tracks
- [ ] Get data from ids
  - [ ] Users
  - [ ] Playlists
    - [ ] Playlist with albums
    - [ ] Playlist without albums
  - [ ] Tracks

===================================================================

1. Foreword
2. API  
- Querying
  - Parameters explaining
  - Playlists
    - Playlist with albums
    - Playlist without albums
  - Users
  - Tracks
  - Everything
- Get data from ids
  - Users
  - Tracks
  - Playlists
    - Playlist with albums
    - Playlist without albums 


## 1. Foreword
This document is written for Soundcloud v2 API, which has not been officially documented. This version of API is subject to change and may already changed at the time of reading.

Please do be informed that the use of V2 API is against the 'Term of use' of SoundCloud in general and should be used for research purposes only.

At the time written, this API is used for an educational project. 

## 2. API
### Querying

#### Parameters explaining

SoundCloud API provides parameters to work with their API, these parameters will be used by combining, concatenating them into request URL, with a separator between them is the `&` symbol.

For example:
```
https://api-v2.soundcloud.com/...?q={YOUR_QUERY}&client_id={YOUR_CLIENT_ID}&.....
```

For this project, only these parameters are needed:
```
q={YOUR_QUERY}  
client_id={YOUR_CLIENT_ID}  
limit={QUERY_RESULT_LIMIT}  (optional)
linked_partitioning=1 
```
- `q={YOUR_QUERY}` is the query you want to search for, if you use `tab`, `space`, ... in the query, it must be replaced with appropriate ASCII encode. Though if you use the `requests` library in python, it will do this for you automatically.
- `client_id={YOUR_CLIENT_ID}` contain your user id, this id is unique to each user. There are many ways to get this field, though the easiest one is through your browser:
   - Open the `inspect` option in Chrome, and go to the network tab.
   - Access [SoundCloud website](https://soundcloud.com/) and look for any network transferring in this tab
   - `client_id` will be in most of these transfer `header`, look around a bit and you will find it.
- `limit={QUERY_RESULT_LIMIT}`, an optional field, if not specified, the default result return of each query will be 1, add this parameter to the request URL if you want to limit the return results.
- `linked_partitioning=1` referring to [SoundCloud pagination](https://developers.soundcloud.com/blog/offset-pagination-deprecated) for more information. Just add it to your initial request.

#### Everything

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
limit={QUERY_RESULT_LIMIT}  
linked_partitioning=1
```
With each parameter separated by `&`, we have the full api query request as follows:
```
https://api-v2.soundcloud.com/search?q={YOUR_QUERY}&client_id={YOUR_CLIENT_ID}&limit={QUERY_RESULT_LIMIT}&linked_partitioning=1
```
An example of a query search for the term `hello world` may be as follows:
```
https://api-v2.soundcloud.com/search?q=hello%20world&client_id=xxxxx&limit=20&linked_partitioning=1
```
This will return the `20` first result for `hello world` (notice that the `xxx...` are to be replaced with actual `client_id`)

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
new_url = response['next_href'] + '&{client_id}'
```

In this case, this url will be:

```
https://api-v2.soundcloud.com/search?query_urn=soundcloud%3Asearch%3Afa128d89a8d44b76817c180aab6fe0f2&limit=20&offset=20&q=hello%20world&client_id=xxxxxxx...
```

This URL will be used to get the next set of results, this process keeps looping until the field `next_href` no longer appears in the response result.

#### Users

SoundCloud api also provide users name search

We will use the following base url to query an users name search:
```
https://api-v2.soundcloud.com/search/users?
```
With these parameters:
```
q={YOUR_QUERY}  
client_id={YOUR_CLIENT_ID}  
limit={QUERY_RESULT_LIMIT}  
linked_partitioning=1
```

With each parameter separated by `&`, we have the full api query request as follows:
```
https://api-v2.soundcloud.com/search/users?q={YOUR_QUERY}&client_id={YOUR_CLIENT_ID}&limit={QUERY_RESULT_LIMIT}&linked_partitioning=1
```
An example of a query search for the term `escatic` may be as follows:
```
https://api-v2.soundcloud.com/search/users?q=escatic&client_id=3jXdkVwgGnCwmB9q5e7qkzpaVm4qjQSn&linked_partitioning=1
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

