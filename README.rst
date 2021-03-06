=============================
ka-lite-zim
=============================

.. image:: https://travis-ci.org/benjaoming/ka-lite-zim.png?branch=master
    :target: https://travis-ci.org/benjaoming/ka-lite-zim

.. image:: https://readthedocs.org/projects/ka-lite-zim/badge/?version=latest
    :target: http://ka-lite-zim.readthedocs.org/en/latest/


OpenZIM export command for ka-lite.


Features
--------

* Exporting the contents of a local `KA Lite <https://learningequality.org/ka-lite/>`_ installation to the `OpenZim <http://www.openzim.org/>`_
* Easy to customize since you use KA Lite to select and download videos
* Creates a .zim file with a single-page webapp containing video player and simple JS-based UI for filtering and searching the videos


Use case and contributions
--------------------------

This project is a Python project but is NOT on PyPi because it's not intended
for a wider audience. So just get the latest master, it should work with the
latest KA Lite release. Please contribute to this project if you have changes to the .zim files that
are available on the `Kiwix website <http://www.kiwix.org/wiki/Content_in_all_languages>`_

The goal of this command is to build an alternative use case of Khan Academy for
the popular offline reader Kiwix, which works for the open standards format
OpenZim. Thus, it can benefit from the data prepared through the KA Lite
software.

While KA Lite is truly built for education, Kiwix is more of an eLibrary. While
Kiwix and OpenZim is more static, KA Lite has its focus on interaction.


Future
------

The export command for KA Lite is the immediate and easiest target. But we hope
to be able to understand the OpenZIM format well enough to build an import
command as well such that KA Lite students can interact with the data packaged
and distributed by zim-packagers.

