from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import

import json
import os
import shutil
import subprocess
import sys
import tempfile

from datetime import datetime
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from kalite.topic_tools import settings as topic_tools_settings, \
    get_content_cache, get_exercise_cache
from kalite.settings.base import CONTENT_ROOT
from kalite import i18n

from kalite_zim.utils import download_video, logger

from fle_utils.general import softload_json

from submarine.parser import parser as submarine_parser
from kalite_zim.anythumbnailer.thumbnail_ import create_thumbnail
from distutils.spawn import find_executable

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
    settings.COMPRESS_CSS_FILTERS = []


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
        make_option(
            '--zimwriterfs', '-z',
            action='store',
            dest='zimwriterfs',
            default=None,
            help="Path to zimwriterfs if it's not on the shell path"
        ),
        make_option(
            '--publisher', '-p',
            action='store',
            dest='publisher',
            default="Learning Equality",
            help="Name of publisher"
        ),
        make_option(
            '--transcode2webm',
            action='store_true',
            dest='transcode2webm',
            default=False,
            help="Name of publisher"
        ),
    )

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("Takes exactly 1 argument")

        dest_file = os.path.abspath(args[0])

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
                logger.info("Clearing directory {}".format(tmp_dir))
                shutil.rmtree(tmp_dir)
            else:
                raise CommandError(
                    "{} not empty, use the -c option to clean it or use an empty destination directory.".format(
                        tmp_dir
                    )
                )

        zimwriterfs = options.get("zimwriterfs", None)
        publisher = options.get("publisher")
        transcode2webm = options.get("transcode2webm")
        ffmpeg = find_executable("ffmpeg")

        if not ffmpeg:
            logger.warning("FFMpeg not found in your path, you won't be able to create missing thumbnails or transcode to webm.")

        if not zimwriterfs:
            zimwriterfs = find_executable("zimwriterfs")
            if not zimwriterfs:
                raise CommandError("Could not find zimwriterfs in your path, try specifying --zimwriterfs=/path")

        if not os.path.exists(zimwriterfs):
            raise CommandError("Invalid --zimwriterfs")

        from kalite_zim import __name__ as base_path
        base_path = os.path.abspath(base_path)
        data_path = os.path.join(base_path, 'data')

        # Where subtitles are found in KA Lite
        subtitle_src_dir = i18n.get_srt_path(language)

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

        def annotate_tree(topic, depth=0, parent=None):
            """
            We need to recurse into the tree in order to annotate elements
            with topic data and exercise data
            """
            children = topic.get('children', [])
            new_children = []
            for child_topic in children:
                if child_topic.get("kind") in ("Video", "Topic"):
                    annotate_tree(child_topic, depth=depth + 1, parent=topic)
                    new_children.append(child_topic)
            topic["children"] = new_children
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

            topic["url"] = topic["id"] + ".html"
            topic["parent"] = parent
            topic["depth"] = depth
            for key in ("child_data", "keywords", "hide", "contains"):
                topic.pop(key, None)

        # 1. Annotate a topic tree
        annotate_tree(topic_tree)

        # 2. Now go through the tree and copy each element into the destination
        # zim file system

        def copy_media(node):
            if node['kind'] == 'Topic':
                # Don't do anything if it's a topic
                pass
            elif node['kind'] == 'Exercise':
                # Exercises cannot be displayed
                node["content"]["available"] = False
            elif node['kind'] == 'Video':

                if node['content']['format'] == "webm":
                    logger.warning("Found a duplicate ID for {}, re-downloading".format(node['id']))
                    node['content']['format'] = "mp4"

                # Available is False by default until we locate the file
                node["content"]["available"] = False
                node_dir = os.path.join(tmp_dir, node["path"])
                if not os.path.exists(node_dir):
                    os.makedirs(node_dir)
                video_file_name = node['id'] + '.' + node['content']['format']
                thumb_file_name = node['id'] + '.png'
                video_file_src = os.path.join(CONTENT_ROOT, video_file_name)
                video_file_dest = os.path.join(node_dir, video_file_name)
                thumb_file_src = os.path.join(CONTENT_ROOT, thumb_file_name)
                thumb_file_dest = os.path.join(node_dir, thumb_file_name)

                if options['download'] and not os.path.exists(video_file_src):
                    logger.info("Video file being downloaded to: {}".format(video_file_src))
                    download_video(
                        node['content']['youtube_id'],
                        node['content']['format'],
                        CONTENT_ROOT,
                    )

                if os.path.exists(video_file_src):
                    if transcode2webm:
                        ffmpeg_pass_log = "/tmp/logfile_vp8.fpf"
                        if os.path.isfile(ffmpeg_pass_log):
                            os.unlink(ffmpeg_pass_log)
                        video_file_name = node['id'] + '.webm'
                        video_file_dest = os.path.join(node_dir, video_file_name)
                        ffmpeg_base_args = [
                            ffmpeg,
                            "-i", video_file_src,
                            "-codec:v", "libvpx",
                            "-quality", "best",
                            "-cpu-used", "0",
                            "-b:v", "300k",
                            "-qmin", "10",  # 10=lowest value
                            "-qmax", "35",  # 42=highest value
                            "-maxrate", "300k",
                            "-bufsize", "600k",
                            "-threads", "8",
                            # "-vf", "scale=-1",
                            "-codec:a", "libvorbis",
                            # "-b:a", "128k",
                            "-aq", "5",
                            "-f", "webm",
                        ]
                        ffmpeg_pass1 = ffmpeg_base_args + [
                            "-an",  # Disables audio, no effect first pass
                            "-pass", "1",
                            "-passlogfile", ffmpeg_pass_log,
                            video_file_dest,
                        ]
                        ffmpeg_pass2 = ffmpeg_base_args + [
                            "-pass", "2",
                            "-y", "-passlogfile", ffmpeg_pass_log,
                            video_file_dest,
                        ]
                        for cmd in (ffmpeg_pass1, ffmpeg_pass2):
                            process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
                            stdout_data, _stderr_data = process.communicate()
                            if process.returncode != 0:
                                logger.error("Error invoking ffmpeg: {}".format((_stderr_data or "") + (stdout_data or "")))
                                logger.error("Command was: {}".format(" ".join(cmd)))
                                raise CommandError("Could not complete transcoding")
                        node['content']['format'] = "webm"
                    else:
                        # If not transcoding, just link the original file
                        os.link(video_file_src, video_file_dest)
                    node["video_url"] = os.path.join(
                        node["path"],
                        video_file_name
                    )
                    copy_media.videos_found += 1
                    logger.info("Videos processed: {}".format(copy_media.videos_found))
                    node["content"]["available"] = True

                    # Create thumbnail if it wasn't downloaded
                    if not os.path.exists(thumb_file_src):
                        fp = create_thumbnail(video_file_src, output_format="png")
                        if fp is None:
                            logger.error("Failed to create thumbnail for {}".format(video_file_src))
                        else:
                            logger.info("Successfully created thumbnail for {}".format(video_file_src))
                            file(thumb_file_src, 'wb').write(fp.read())

                    # Handle thumbnail
                    if os.path.exists(thumb_file_src):
                        node["thumbnail_url"] = os.path.join(
                            node["path"],
                            node['id'] + '.png'
                        )
                        os.link(thumb_file_src, thumb_file_dest)
                    else:
                        node["thumbnail_url"] = None

                    subtitle_srt = os.path.join(
                        subtitle_src_dir,
                        node['id'] + '.srt'
                    )
                    if os.path.isfile(subtitle_srt):
                        subtitle_vtt = os.path.join(
                            node_dir,
                            node['id'] + '.vtt'
                        )
                        # Convert to .vtt because this format is understood
                        # by latest video.js and the old ones that read
                        # .srt don't work with newer jquery etc.
                        submarine_parser(subtitle_srt, subtitle_vtt)
                        if not os.path.exists(subtitle_vtt):
                            logger.warning("Subtitle not converted: {}".format(subtitle_srt))
                        else:
                            logger.info("Subtitle convert from SRT to VTT: {}".format(subtitle_vtt))
                            node["subtitle_url"] = os.path.join(
                                node["path"],
                                node['id'] + '.vtt'
                            )

                else:
                    if options['download']:
                        logger.error("File not found or downloaded: {}".format(video_file_src))
            else:
                logger.error("Invalid node, kind: {}".format(node.get("kind", None)))
                # Exercises cannot be displayed
                node["content"] = {"available": False}

            new_children = []
            for child in node.get('children', []):
                copy_media(child)
                empty_topic = child["kind"] == "Topic" and not child.get("children", [])
                unavailable_video = child["kind"] == "Video" and not child.get("content", {}).get("available", False)
                if not (empty_topic or unavailable_video):
                    new_children.append(child)
            node['children'] = new_children
        copy_media.videos_found = 0

        def render_topic_pages(node):

            parents = [node] if node.get("children") else []
            parent = node["parent"]
            while parent:
                parents.append(parent)
                parent = parent["parent"]

            # Finally, render templates into the destination
            template_context = {
                "topic_tree": topic_tree,
                "topic": node,
                "parents": parents
            }
            with i18n.translate_block(language):
                topic_html = render_to_string("kalite_zim/topic.html", template_context)
            # Replace absolute references to '/static' with relative
            topic_html = topic_html.replace("/static", "static")

            dest_html = os.path.join(tmp_dir, node["id"] + ".html")
            logger.info("Rendering {}".format(dest_html))

            open(dest_html, "w").write(topic_html)

            render_topic_pages.pages_rendered += 1

            for child in node.get('children', []):
                render_topic_pages(child)
        render_topic_pages.pages_rendered = 0

        logger.info("Hard linking video files from KA Lite...")
        copy_media(topic_tree)

        sys.stderr.write("\n")
        logger.info("Done!")

        # Configure django-compressor
        compressor_init(os.path.join(base_path, 'static'))

        # Finally, render templates into the destination
        template_context = {
            "topic_tree": topic_tree,
            "welcome": True,
        }

        with i18n.translate_block(language):
            welcome_html = render_to_string("kalite_zim/welcome.html", template_context)
            about_html = render_to_string("kalite_zim/about.html", template_context)
        # Replace absolute references to '/static' with relative
        welcome_html = welcome_html.replace("/static", "static")
        about_html = about_html.replace("/static", "static")

        # Write the welcome.html file
        open(os.path.join(tmp_dir, 'welcome.html'), 'w').write(welcome_html)
        open(os.path.join(tmp_dir, 'about.html'), 'w').write(about_html)

        # Render all topic html files
        render_topic_pages(topic_tree)

        # Copy in static data after it's been handled by django compressor
        # (this happens during template rendering)

        shutil.copytree(os.path.join(base_path, 'static'), os.path.join(tmp_dir, 'static'))

        ending = datetime.now()
        duration = int((ending - beginning).total_seconds())
        logger.info("Total number of videos found: {}".format(copy_media.videos_found))
        logger.info("Total number of topic pages created: {}".format(render_topic_pages.pages_rendered))

        logger.info("Invoking zimwriterfs, writing to: {}".format(dest_file))

        zimwriterfs_args = (
            zimwriterfs,
            "--welcome", "welcome.html",
            "--favicon", "static/img/ka_leaf.png",
            "--publisher", publisher,
            "--creator", "KhanAcademy.org",
            "--description", "Khan Academy ({})".format(language),
            "--description", "Videos from Khan Academy",
            "--language", language,
            tmp_dir,
            dest_file,
        )

        process = subprocess.Popen(zimwriterfs_args, stdout=subprocess.PIPE)
        stdout_data, _stderr_data = process.communicate()

        if process.returncode != 0:
            logger.error("Error invoking zimwriterfs: {}").format(_stderr_data + stdout_data)

        logger.info(
            "Duration: {h:} hours, {m:} minutes, {s:} seconds".format(
                h=duration // 3600,
                m=(duration % 3600) // 60,
                s=duration % 60,
            )
        )
