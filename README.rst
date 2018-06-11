Radiocut.fm downloader
======================

Radiocut_ is an amazing service that records radio stations from in 24x7 basis, and let you create cuts for an specific station and time.

This script retrieves and merges the chunks that compose an audiocut,




Install
-------

::

    $ [sudo] pip install radiocut_downloader


Usage
------

::

    tin@morochita:~$ radiocut -h
    radiocut.fm downloader

    Usage:
        radiocut <audiocut_or_podcast> [<output-file-name>]
                        [--verbose] [--background=<path-to-image>] [--join] [--duration=<duration>]

    Options:
      -h --help                         Show this screen.
      --background=<path-to-image>      If given, produce a video with this image as background
      --join                            Concatenate podcast's cuts as a single file
      --duration=<duration>             The length to download (in seconds)

Examples
--------

::

    $ radiocut http://radiocut.fm/audiocut/macri-gato/    # macri-gato.mp3

    $ radiocut http://radiocut.fm/audiocut/macri-gato/  --verbose    # macri-gato.mp3 with verbose output

    $ radiocut http://radiocut.fm/pdc/tin_nqn_/test       # as many mp3 files, as "cuts" in the podcast

    $ radiocut http://radiocut.fm/pdc/tin_nqn_/test  --join    # test.mp3 joining all the cuts sequentially


    $ radiocut http://radiocut.fm/pdc/tin_nqn_/test  --join --background=~/Images/black-cat.jpg   # test.mp4

    # get any fragment
    $ radiocut http://radiocut.fm/radiostation/nacional870/listen/2017/07/08/10/00/00/ custom_2m_cut --duration=120

    # get shows
    $ radiocut https://radiocut.fm/radioshow/el-lobby/


.. attention::

    radiocut is a hard-working tiny start-up, its service is great and
    they deserve all our respect.

    If you need to download audios for professional purposes,
    you should consider to get a `premium account <http://radiocut.fm/premium/>`_.



.. _Radiocut: http://radiocut.fm
