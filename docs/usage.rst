========
Usage
========

#. Open up KA Lite and make sure that the correct language pack and videos have been downloaded.

#. Now you can run the OpenZim export command like this::
    
    kalite manage export2zim --language=en output.zim
    
.. warning ::
    We first created ka-lite-zim for ka-lite 0.15.x, and in case you are running
    an older version of KA Lite or the unreleased 0.16, you should take care if
    these versions of ka-lite already store data in ``~/.kalite``.
    Run commands differently to use different home directories, e.g.
    ``KALITE_HOME=~/.kalite_zim kalite manage start`` and
    ``KALITE_HOME=~/.kalite_zim kalite manage export2zim``
    
    Remember your also need to change ``settings.py`` in the new user folder.