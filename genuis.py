from tokens import ACCESS_TOKEN
import requests

class GeniusNotFound(Exception):
    pass

class Genius:
    def __init__(self):
        self.base_url = 'http://api.genius.com'
        self.headers = {'Authorisation': f'Bearer {ACCESS_TOKEN}'}

    def get_song_id(self, song_title: str, artist_name: str) -> int | None:
        search_url = self.base_url + '/search'
        data = {'q': song_title}

        response = requests.get(search_url, params=data, headers=self.headers).json()

        if response['meta']['status'] == 200:
            for hit in response['response']['hits']:
                if hit['result']['primary_artist']['name'].lower() == artist_name.lower():
                    return hit['result']['id']
        else:
            raise GeniusNotFound

    def get_song(self, id):
        song_url = self.base_url + '/song/'
        response = requests.get(song_url + str(id), headers=self.headers).json()

        if response['meta']['status'] == 200:
            return response['response']['song']

