import logging
import os
import sys

from plexnowplaying.config.configmanager import ConfigManager

if os.getenv('devconfig'):
    config = os.getenv('devconfig')
else:
    config = 'config.ini'

config = ConfigManager(config)
