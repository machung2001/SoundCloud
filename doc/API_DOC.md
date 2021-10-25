# SoundCloud API (v2) Unofficial Documents
0. Documents progress
- [x] Foreword
- [ ] Querying
  - [ ] Parameters explaining
  - [ ] Playlists
    - [ ] Playlist with albums
    - [ ] Playlist without albums
  - [ ] Users
  - [ ] Tracks
  - [x] Everything
  
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



##1. Foreword
This document is written for Soundcloud v2 API, which has not been officially documented. This version of API is subject to change at may already be changed at the time of readings.

Please do be informed that the use of V2 API is against the 'Term of use' of SoundCloud in general and should be used for research purposes only.

At the time written, this API is used for an educational project. 

##2. API
###Querying
####Everything

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

- `collection` is a list of results with the length of the requested `limit` parameter, in this case, the `20` item will be returned and stored in this field, we can start extracting this as data.

- `total_result` is the total result of the search query
- `next_href` however, is what we must care about, for this contain a link of the next `20` result (or `limit` parameter value).

Parameter `next_href` will be concatenated with `client_id` to produce the next url for api request:
```python
new_url = response['next_href'] + '&{client_id}'
```

This URL will be used to get the next set of results, this process keeps looping until the field `next_href` no longer appears in the response result.
