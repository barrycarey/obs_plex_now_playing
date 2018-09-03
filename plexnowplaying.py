import argparse

from plexnowplaying import PlexNowPlaying

parser = argparse.ArgumentParser(description="Report Plex Currently Playing Music For Use in OBS ")
parser.add_argument('--server', default=None, dest='server', help='Address of the server to connect to')
parser.add_argument('--username', default=None, dest='username', help='Plex Username')
parser.add_argument('--password', default=None, dest='password', help='Plex Username')
args = parser.parse_args()

# TODO - Validate we got the required args

plex = PlexNowPlaying(args.username, args.password, args.server)

plex.run()