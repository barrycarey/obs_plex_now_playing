import base64
import json
import logging
import sys
import time
from urllib.request import Request, urlopen

from plexapi.server import PlexServer
from requests import HTTPError

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

    def __init__(self, username, password, server):
        self.username = username
        self.password = password
        self.server_addr = server
        self.plex = self.connect_to_server()

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
            player = stream.players[0]
            if stream.type != 'track':
                log.debug('Skipping media type %s: %s', stream.type, stream.title)
                continue
            elif self.username != user:
                log.debug('Skipping music played by different user (%s)', user)

            result['artist'] = stream.grandparentTitle
            result['album'] = stream.parentTitle
            result['title'] = stream.title
            result['art'] = stream.parentThumb
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
        try:
            with open(config.playing_file, 'w') as f:
                f.write(out_string)
                log.debug('Successfully wrote now playing file')
        except Exception as e:
            log.exception('Failed to write now playing file', exc_info=True)

        try:
            with open(config.art_file, 'w') as f:
                f.write(data['art'])
                log.debug('Successfully wrote now art file')
        except Exception as e:
            log.exception('Failed to write art file', exc_info=True)


    def format_now_playing(self):
        pass

    def connect_to_server(self):
        base_url = 'http://{}:32400'.format(self.server_addr)
        plex = PlexServer(base_url, self.get_auth_token(self.username, self.password))

        return plex

    def get_auth_token(self, username, password):
        """
        Make a reqest to plex.tv to get an authentication token for future requests
        :param username: Plex Username
        :param password: Plex Password
        :return: str
        """

        log.info('Getting Auth Token For User {}'.format(username))

        auth_string = '{}:{}'.format(username, password)
        base_auth = base64.encodebytes(bytes(auth_string, 'utf-8'))
        req = Request('https://plex.tv/users/sign_in.json')

        headers = {
            'X-Plex-Client-Identifier': 'Plex InfluxDB Collector',
            'X-Plex-Product': 'Plex InfluxDB Collector',
            'X-Plex-Version': '1',
        }

        for k, v in headers.items():
            req.add_header(k, v)

        req.add_header('Authorization', 'Basic {}'.format(base_auth[:-1].decode('utf-8')))

        try:
            result = urlopen(req, data=b'').read()
        except HTTPError as e:
            print('Failed To Get Authentication Token')
            if e.code == 401:
                log.error('Failed to get token due to bad username/password')
            else:
                print('Maybe this will help:')
                print(e)
                log.error('Failed to get authentication token.  No idea why')
            sys.exit(1)

        output = json.loads(result.decode('utf-8'))

        # Make sure we actually got a token back
        if 'authToken' in output['user']:
            return output['user']['authToken']
        else:
            print('Something Broke \n We got a valid response but for some reason there\'s no auth token')
            sys.exit(1)

    def run(self):
        while True:
            now_playing = self.get_now_playing()
            if now_playing:
                self.write_now_playing(now_playing)
            time.sleep(2)
