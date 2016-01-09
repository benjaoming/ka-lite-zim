from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import

import os
import urllib

from django.conf import settings
from fle_utils.videos import get_outside_video_urls

from kalite_zim import __name__ as base_path
base_path = os.path.abspath(base_path)

EMPTY_THUMBNAIL = os.path.join(base_path, "data", "no_thumb.png")

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
        __, response = urllib.urlretrieve(url, video_filename)
        if not response.type.startswith("video"):
            raise Exception("Video download failed: {}".format(url))

        __, response = urllib.urlretrieve(thumb_url, thumbnail_filename)
        if not response.type.startswith("image"):
            open(thumbnail_filename, "wb").write(
                open(EMPTY_THUMBNAIL, "rb").read()
            )

    except Exception:
        delete_download_garbage()
        raise
