**Plex Now Playing For OBS**
------------------------------

A tool to pull the currently playing song and album art from Plex and save to a file.  Perfect for use with OBS for streaming 

**Usage**

Enter your desired information in config.ini and run plexnowplaying.py

## Configuration within config.ini

#### GENERAL
|Key            |Description                                                                                                         |
|:--------------|:-------------------------------------------------------------------------------------------------------------------|
|Delay          |Delay between updating metrics                                                                                      |
|Output_Dir     |Directory to write output files to                                                                                  |
|Playing_File   |Name of the file to store song name                                                                                 |
|Art_File       |Name of album art file (should end with .png for Plex)                                                              |
|Thumb_Size     |Size in pixels to make the album art file                                                                           |                                                                                            |
#### PLEX
|Key            |Description                                                                                                         |
|:--------------|:-------------------------------------------------------------------------------------------------------------------|
|Username       |Plex username                                                                                                       |
|Password       |Plex Password                                                                                                       |
|Server         |Plex server IP address                                                     |
#### LOGGING
|Key            |Description                                                                                                         |
|:--------------|:-------------------------------------------------------------------------------------------------------------------|
|Level          |Minimum type of message to log.  Valid options are: critical, error, warning, info, debug                           |


***Requirements***

* Python 3.x

Run `pip install -r requirements.txt`

Python Packages
* [plexapi](https://pypi.org/project/PlexAPI/)


