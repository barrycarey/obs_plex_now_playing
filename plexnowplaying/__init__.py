import base64
import json
import logging
import os
import sys
import time
from urllib.request import Request, urlopen

import requests
from PIL import Image
from plexapi.server import PlexServer
from requests import HTTPError
from requests.auth import HTTPBasicAuth

from plexnowplaying.config import config
from plexnowplaying.logfilters import SingleLevelFilter

log = logging.getLogger(__name__)
log.setLevel('DEBUG')
formatter = logging.Formatter('%(asctime)s%(levelname)s:%(module)s:%(funcName)s:%(lineno)d: %(message)s')

general_handler = logging.StreamHandler(sys.stdout)
general_filter = SingleLevelFilter(logging.INFO, False)
general_handler.setFormatter(formatter)
general_handler.addFilter(general_filter)
log.addHandler(general_handler)

error_handler = logging.StreamHandler(sys.stderr)
error_filter = SingleLevelFilter(logging.WARNING)
error_handler.setFormatter(formatter)
error_handler.addFilter(error_filter)
log.addHandler(error_handler)

log.propagate = False

class PlexNowPlaying:

    # TODO - Convert all HTTP requests to use requests lib
    def __init__(self):
        # TODO - Dirty dirty, fix this at some point.  Need to revist token handling
        self.token = None
        self.token = self.get_auth_token(config.plex_user, config.plex_password)
        self.plex = self.connect_to_server()

    def download_album_art(self, url):
        """
        Take an Plex URL for album art and download
        :param url: full Plex URL
        :return: None
        """
        headers = self.get_default_headers(token=self.token)
        log.debug('Attempting to download album art from %s', url)
        result = requests.get(url, headers=headers)
        if result.status_code != 200:
            log.error('Error getting album art.  Unexpected response code %s', result.status_code)
            return

        file_name = os.path.join(config.output_dir, 'art_orig.png')
        try:
            with open(file_name, 'wb') as f:
                f.write(result.content)
            log.info('Successfully updated album art')
            self.resize_album_art(file_name)
        except Exception as e:
            log.exception('Failed to save album art', exc_info=True)

    def resize_album_art(self, path):
        """
        Resize the downloaded album art to ensure consistent size in OBS
        :param path: str - Path to file
        :return: None
        """
        if os.path.isfile(path):
            # TODO - Exceptions
            img = Image.open(path)
            # TODO - Refactor - Taken from https://opensource.com/life/15/2/resize-images-python
            basewidth = config.thumb_size
            wpercent = (basewidth / float(img.size[0]))
            hsize = int((float(img.size[1]) * float(wpercent)))
            img = img.resize((basewidth, hsize), Image.ANTIALIAS)

            try:
                os.remove(path)
            except PermissionError as e:
                log.error('Album art is locked, cannot remove')

            img.save(os.path.join(config.output_dir, config.art_file))
            log.debug('Resized provided album art')
        else:
            log.error('Provided Album Art path is invalid.  Path: %s', path)

    def get_now_playing(self):
        """
        Find currently playing music
        :return:
        """
        result = {}
        sessions = self.plex.sessions()
        log.debug('Loaded %s active streams', len(sessions))
        for stream in sessions:
            user = stream.usernames[0]
            if stream.type != 'track':
                log.debug('Skipping media type %s: %s', stream.type, stream.title)
                continue
            elif config.plex_user != user:
                log.debug('Skipping music played by different user (%s)', user)

            result['artist'] = stream.grandparentTitle
            result['album'] = stream.parentTitle
            result['title'] = stream.title
            if stream.parentThumb:
                result['art'] = 'http://{}:32400{}'.format(config.plex_server, stream.parentThumb)
            elif stream.grandparentThumb:
                result['art'] = 'http://{}:32400{}'.format(config.plex_server, stream.grandparentThumb)
            else:
                result['art'] = None
            break
        log.debug('Now Playing %s', result)
        return result

    def write_now_playing(self, data):
        """
        Output the now playing data to file
        :param data: Dict
        :return: None
        """
        out_string = '{} - {}'.format(data['artist'], data['title'])
        now_playing = os.path.join(config.output_dir, config.playing_file)

        if os.path.isfile(now_playing):
            with open(now_playing, 'r') as f:
                content = f.read()
                if content == out_string:
                    log.debug('Skipping now playing update')
                    return

        try:
            with open(now_playing, 'w') as f:
                f.write(out_string)
                log.info('Set Now Playing To %s', out_string)
        except Exception as e:
            log.exception('Failed to write now playing file', exc_info=True)

        if data['art']:
            self.download_album_art(data['art'])

    def format_now_playing(self):
        pass

    def connect_to_server(self):
        """
        Create a PlexServer object with an active connection to the server and return the object
        :return: PlexServer
        """
        if not self.token:
            log.error('No API token currently set')
            return
        base_url = 'http://{}:32400'.format(config.plex_server)
        plex = PlexServer(base_url, self.get_auth_token(config.plex_user, config.plex_password))
        return plex

    def get_auth_token(self, username, password):

        if self.token:
            return self.token

        headers = self.get_default_headers()
        try:
            r = requests.post('https://plex.tv/users/sign_in.json', headers=headers, auth=HTTPBasicAuth(username, password))
        except Exception as e:
            # TODO - More Specific exception
            log.exception('Error getting auth token', exc_info=True)
            return

        if r.status_code != 201:
            log.error('Unexpected response code from Plex API. Response Code %s', r.status_code)
            return

        return json.loads(r.text)['user']['authToken']

    def get_default_headers(self, token=None):
        """
        Return the default headers need to make a request to Plex.
        :param token: Existing token
        :return: dict
        """

        log.debug('Adding Request Headers')

        headers = {
            'X-Plex-Client-Identifier': 'Plex InfluxDB Collector',
            'X-Plex-Product': 'Plex InfluxDB Collector',
            'X-Plex-Version': '1'
        }

        if token:
            headers['X-Plex-Token'] = token

        return headers

    def run(self):

        #self.get_auth_token_test(config.plex_user, config.plex_password)
        while True:
            now_playing = self.get_now_playing()
            if now_playing:
                self.write_now_playing(now_playing)
            time.sleep(2)
