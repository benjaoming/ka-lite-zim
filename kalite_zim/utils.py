from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import

import logging
import os
import urllib

from colorlog import ColoredFormatter
from django.conf import settings
from fle_utils.videos import get_outside_video_urls

from . import __name__ as base_path

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
        retries = 0
        while retries < 5:
            try:
                __, response = urllib.urlretrieve(url, video_filename)
            except:
                delete_download_garbage()
                retries += 1
                if retries >= 5:
                    raise
                else:
                    logger.warning("Retrying {}".format(retries))
        if not response.type.startswith("video"):
            raise Exception("Video download failed: {}".format(url))

        __, response = urllib.urlretrieve(thumb_url, thumbnail_filename)
        if not response.type.startswith("image"):
            logger.warning("Thumbnail missing, tried: {}".format(thumb_url))

    except (Exception, KeyboardInterrupt):
        delete_download_garbage()
        raise
