from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import

import logging
import os
import time
import urllib

from colorlog import ColoredFormatter
from django.conf import settings
from fle_utils.videos import get_outside_video_urls

from . import __name__ as base_path
import socket
import traceback

base_path = os.path.abspath(base_path)


LOG_LEVEL = logging.DEBUG
LOGFORMAT = "  %(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"
logging.root.setLevel(LOG_LEVEL)
formatter = ColoredFormatter(LOGFORMAT)
stream = logging.StreamHandler()
stream.setLevel(LOG_LEVEL)
stream.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
logger.addHandler(stream)
logger.propagate = False


class DownloadError(Exception):
    pass


def download_video(youtube_id, video_format, dest_dir):
    """
    Fetch a video from the default
    """

    download_url = ("http://%s/download/videos/" % (settings.CENTRAL_SERVER_HOST)) + "%s/%s"

    url, thumb_url = get_outside_video_urls(youtube_id, download_url=download_url, format=video_format)

    video_filename = os.path.join(dest_dir, "{}.{}".format(youtube_id, video_format))
    thumbnail_filename = os.path.join(dest_dir, "{}.png".format(youtube_id))

    def delete_download_garbage():
        if os.path.isfile(video_filename):
            os.unlink(video_filename)
        if os.path.isfile(thumbnail_filename):
            os.unlink(thumbnail_filename)

    try:
        while True:
            try:
                logger.info("Let's try and fetch {}".format(url))
                __, response = urllib.urlretrieve(url, video_filename)
                if str(response.status) == '404':
                    delete_download_garbage()
                    logger.error("404 for: {}".format(url))
                    return  # Nothing to do
                if not response.type.startswith("video"):
                    logger.error("Video download failed with status {}: {}".format(response.status or "None", url))
                    raise DownloadError()
                break
            except (DownloadError, socket.error, IOError):
                delete_download_garbage()
                logger.warning("Download failed, retrying again in 2 seconds.")
                time.sleep(2)
            except IOError:
                delete_download_garbage()
                logger.warning("Download failed, IO error, retrying again in 2 seconds.")
                logger.error(traceback.format_exc())
                time.sleep(2)

        __, response = urllib.urlretrieve(thumb_url, thumbnail_filename)
        if not response.type.startswith("image"):
            logger.warning("Thumbnail missing, tried: {}".format(thumb_url))

    except (Exception, KeyboardInterrupt):
        delete_download_garbage()
        raise
