import configparser
import os
import sys
from urllib.error import URLError
from urllib.request import urlopen


class ConfigManager:

    def __init__(self, config):

        print('Loading config: ' + config)

        config_file = os.path.join(os.getcwd(), config)
        if os.path.isfile(config_file):
            self.config = configparser.ConfigParser()
            self.config.read(config_file)
        else:
            print('ERROR: Unable To Load Config File: {}'.format(config_file))
            sys.exit(1)

        self._load_config_values()
        self._validate_plex_server()
        print('Configuration Successfully Loaded')

    def _load_config_values(self):

        # General
        self.delay = self.config['GENERAL'].getint('Delay', fallback=2)
        self.monitor_directory = self.config['GENERAL']['Monitor_Directory']
        self.playing_file = self.config['GENERAL']['Playing_File']
        self.art_file = self.config['GENERAL']['Art_File']
        self.thumb_size = self.config['GENERAL'].getint('Thumb_Size', fallback=500)

        # Plex
        self.plex_user = self.config['PLEX']['Username']
        self.plex_password = self.config['PLEX'].get('Password', raw=True)
        self.plex_server = self.config['PLEX']['Server']

        #Logging
        self.logging_level = self.config['LOGGING']['Level'].upper()

    def _validate_plex_server(self):
        """
        Make sure the servers provided in the config can be resolved.  Abort if they can't
        :return:
        """
        failed_servers = []

        server_url = 'http://{}:32400'.format(self.plex_server)
        try:
            urlopen(server_url)
        except URLError as e:
            # If it's 401 it's a valid server but we're not authorized yet
            if hasattr(e, 'code') and e.code == 401:
                print('Provided Plex server is valid')
                return
            else:
                print('Unable to connect to provided Plex server.  Check address and try again')
                sys.exit(1)


