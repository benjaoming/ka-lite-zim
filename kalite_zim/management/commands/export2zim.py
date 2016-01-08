from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import

import json
import logging
import os
import sys
import tempfile

from colorlog import ColoredFormatter
from datetime import datetime
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _

from kalite.topic_tools import settings as topic_tools_settings, \
    get_content_cache, get_exercise_cache
from kalite.settings.base import CONTENT_ROOT
from kalite import i18n

from kalite_zim.utils import download_video

from fle_utils.general import softload_json
import shutil
from django.template.loader import render_to_string

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

def compressor_init(input_dir):

    settings.COMPRESS_PRECOMPILERS = (
        ('text/x-scss', 'django_libsass.SassCompiler'),
    )

    settings.STATICFILES_FINDERS = (
        'django.contrib.staticfiles.finders.FileSystemFinder',
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
        'compressor.finders.CompressorFinder',
    )

    settings.COMPRESS_ROOT = input_dir
    settings.COMPRESS_OUTPUT_DIR = ''


class Command(BaseCommand):
    args = ('zimfile')
    help = 'Export video and meta data of your KA Lite installation to OpenZim'  # @ReservedAssignment
    option_list = BaseCommand.option_list + (
        make_option(
            '--language', '-l',
            action='store',
            dest='language',
            default='en',
            help='Select which language (videos and meta data) to export'
        ),
        make_option(
            '--tmp-dir', '-t',
            action='store',
            dest='tmp_dir',
            default='',
            help='Directory for the temporary zim filesystem'
        ),
        make_option(
            '--test',
            action='store_true',
            dest='test',
            help='Use test data'
        ),
        make_option(
            '--clear', '-c',
            action='store_true',
            dest='clear',
            default=False,
            help='Force clearing temporary fs and output destinations before write'
        ),
        make_option(
            '--download', '-d',
            action='store_true',
            dest='download',
            default=False,
            help='Instead of skipping videos that are not available, download them to KA Lite.'
        ),
    )

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("Takes exactly 1 argument")

        dest_file = args[0]

        logger.info("Starting up KA Lite export2zim command")
        beginning = datetime.now()
        logger.info("Begin: {}".format(beginning))

        language = options.get('language')
        if not language:
            raise CommandError("Must specify a language!")

        if not options.get('tmp_dir'):
            tmp_dir = os.path.join(tempfile.gettempdir(), 'ka-lite-zim_{}'.format(language))
        else:
            tmp_dir = options.get('tmp_dir')

        tmp_dir = os.path.abspath(tmp_dir)

        if os.path.exists(tmp_dir) and os.listdir(tmp_dir):
            if options['clear']:
                shutil.rmtree(tmp_dir)
            else:
                raise CommandError(
                    "{} not empty, use the -c option to clean it or use an empty destination directory.".format(
                        tmp_dir
                    )
                )

        from kalite_zim import __name__ as base_path
        base_path = os.path.abspath(base_path)
        data_path = os.path.join(base_path, 'data')

        video_dir = os.path.join(tmp_dir, 'videos')
        thumbnail_dir = os.path.join(tmp_dir, 'thumbnails')

        for _dir in [video_dir, thumbnail_dir]:
            if not os.path.exists(_dir):
                os.makedirs(_dir)

        logger.info("Will export videos for language: {}".format(language))
        logger.info("Preparing KA Lite topic tree...")

        # Use live data
        if not options.get('test'):
            # This way of doing things will be deprecated in KA Lite 0.16
            topic_tree_json_path = topic_tools_settings.TOPICS_FILEPATHS.get('khan')
            content_cache = get_content_cache(language=language, annotate=True)
            exercise_cache = get_exercise_cache(language=language)
        # Use test data
        else:
            topic_tree_json_path = os.path.join(data_path, 'test_topics.json')
            content_cache = json.load(
                open(os.path.join(data_path, 'test_content.json'))
            )
            exercise_cache = json.load(
                open(os.path.join(data_path, 'test_exercise.json'))
            )

        topic_tree = softload_json(topic_tree_json_path, logger=logger.debug, raises=False)

        content_json_output = {}
        exercise_json_output = {}

        def annotate_tree(topic, depth=0):
            """
            We need to recurse into the tree in order to annotate elements
            with topic data and exercise data
            """
            children = topic.get('children', [])
            for child_topic in children:
                annotate_tree(child_topic, depth=depth + 1)
            if topic.get("kind") == "Exercise":
                topic['exercise'] = exercise_cache.get(topic.get("id"), {})
                exercise_json_output[topic.get("id")] = topic['exercise']
            elif topic.get("kind") == "Topic":
                pass
            else:
                topic['exercise'] = None
                topic['content'] = content_cache.get(topic.get("id"), {})
                content_json_output[topic.get("id")] = topic['content']
                if not topic['content']:
                    logger.error('No content!?, id is: {}'.format(topic.get('id')))

            # Translate everything for good measure
            with i18n.translate_block(language):
                topic["title"] = _(topic.get("title", ""))
                topic["description"] = _(topic.get("description", "")) if topic.get("description") else ""

        # 1. Annotate a topic tree
        annotate_tree(topic_tree)

        # 2. Now go through the tree and copy each element into the destination
        # zim file system
        
        videos_found = 0

        def copy_media(node):
            if node['kind'] == 'Video':
                if 'content' not in node:
                    logger.error('No content key for video {}'.format(node['id']))
                else:
                    video_file_name = node['id'] + '.' + node['content']['format']
                    thumb_file_name = node['id'] + '.png'
                    video_file_src = os.path.join(CONTENT_ROOT, video_file_name)
                    video_file_dest = os.path.join(video_dir, video_file_name)
                    thumb_file_src = os.path.join(CONTENT_ROOT, thumb_file_name)
                    thumb_file_dest = os.path.join(thumbnail_dir, thumb_file_name)

                    if options['download'] and not os.path.exists(video_file_src):
                        logger.info("Video file being downloaded to: {}".format(video_file_src))
                        download_video(
                            node['content']['youtube_id'],
                            node['content']['format'],
                            CONTENT_ROOT,
                        )

                    if os.path.exists(video_file_src):
                        os.link(video_file_src, video_file_dest)
                        os.link(thumb_file_src, thumb_file_dest)
                        videos_found += 1
                        logger.info("Videos found: {}".format(videos_found))
                    else:
                        logger.error("File not found: {}".format(video_file_src))
            for child in node.get('children', []):
                copy_media(child)

        logger.info("Hard linking video files from KA Lite...")
        copy_media(topic_tree)
        sys.stderr.write("\n")
        logger.info("Done!")

        # Configure django-compressor
        compressor_init(os.path.join(base_path, 'static'))

        # Finally, render templates into the destination
        template_context = {
            "topic_tree": topic_tree,
        }

        welcome_html = render_to_string("kalite_zim/welcome.html", template_context)
        # Replace absolute references to '/static' with relative
        welcome_html = welcome_html.replace("/static", "static")
        open(os.path.join(tmp_dir, 'welcome.html'), 'w').write(welcome_html)

        # Copy in static data after it's been handled by django compressor
        # (this happens during template rendering)

        shutil.copytree(os.path.join(base_path, 'static'), os.path.join(tmp_dir, 'static'))

        ending = datetime.now()
        duration = int((ending - beginning).total_seconds())
        logger.info(
            "Duration: {h:} hours, {m:} minutes, {s:} seconds".format(
                h=duration // 3600,
                m=(duration % 3600) // 60,
                s=duration % 60,
            )
        )
