========
Usage
========

.. note ::
    Your system should have ``/usr/bin/ffmpeg`` available to generate thumbnails
    on the fly. There are several thumbnails missing in the collection so this
    is recommended.

To see all options, run::
    
    kalite manage help export2zim

Manually select videos
----------------------

#. Run ``kalite start`` and go to your browser, setting up KA Lite and selecting
   the videos you need and downloading them.

#. When KA Lite has the videos, you want, run this command

    kalite manage export2zim --language=en output.zim


Automatically downloading all videos
------------------------------------

#. Run ``kalite start``, you may run ``kalite stop`` after, but the server
   has to be initialized firstly.

#. To download a language pack for KA Lite without using the interface, run::

    kalite manage languagepackdownload --language=en --commandline

#. Now you can run the OpenZim export command like this::
    
    kalite manage export2zim --language=en --download output.zim

.. note ::
    We use a temporary directory to create the .zim file and hard link all the
    videos. Therefore, if your ``/tmp`` folder and KA Lite data are on different
    devices, you can have problems. Use ``--tmp-dir=./tmp`` to specify a
    different location for temporary files.

.. warning ::
    We first created ka-lite-zim for ka-lite 0.15.x, and in case you are running
    an older version of KA Lite or the unreleased 0.16, you should take care if
    these versions of ka-lite already store data in ``~/.kalite``.
    Run commands differently to use different home directories, e.g.
    ``KALITE_HOME=~/.kalite_zim kalite manage start`` and
    ``KALITE_HOME=~/.kalite_zim kalite manage export2zim``
    
    Remember your also need to change ``settings.py`` in the new user folder.


Testing
-------

The data sets are quite huge, so if you are developing and testing, use the
``--test`` flag and everything uses bogus JSON source data.
