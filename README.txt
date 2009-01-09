HME/VLC video streamer, v2.7
by William McBrine <wmcbrine@gmail.com>
January 9, 2009

A simple streaming HME server for the TiVo Series 3 or HD.

Uses ports 9043 and 9044. Tested on Ubuntu Linux 8.04, Mac OS X 10.4,
and Windows XP.

Requirements:

- TiVo S3 or HD with 9.4 or later software

- Python 2.4 or later (2.5 or later recommended)
  http://python.org/

- VLC (0.8.6 recommended)
  http://www.videolan.org/

Use:

- Unzip
- (Optional) Edit config.ini to point to your files
- Run start.py
- Go to the Music, Photos and More menu on your TiVo

Stop:

- Ctrl-C on Linux or Mac; close the window on Windows. (Ctrl-C does an
  orderly shutdown that removes the app from the menu, but unfortunately
  this doesn't work in Windows.)

More info:

Streams can require VLC to reencode/rebroadcast them, or not. For the 
TiVo to use a stream directly, without VLC, the stream must be MPEG-2 or 
MPEG-4, and served via http. Entries for new streams or shares can be 
created in config.ini.

Only one instance of VLC will be run at a time, but it can support 
multiple TiVos watching the same stream, with little additional 
overhead. However, two different TiVos can't simultaneously watch two 
different streams if they both require VLC.

Changes:

2.7 -- If files or streams fail a pass-through (non-VLC) attempt, try
       again using VLC, if available. Suggested by TCF user "goodtrips".
       (Not as helpful as one would expect -- VLC is refusing to
       transcode some things that it can play perfectly well.)

       Added a few more recognized extensions (let me know if there's
       one you want).

       Page Up / Page Down was messed up.

       Lists with more than 256 items caused an exception. Reported
       by "Allanon".

2.6 -- Make sure VLC is shut down even when the HME/VLC session ends
       abnormally. Suggested by TCF user "texaslabrat".

       Use AC3 instead of MPEG audio -- should allow for more channels
       and higher quality.

       Added support for setting audio bitrate via config.ini; default
       is 384.

       Rounded end for the highlight bar; shaded background area now
       stays in place, as in TiVo's own menus; delay when sliding the
       menu in is more reliable.

2.5 -- Server port and video bitrate can be set in config.ini; the vlc
       path is taken from the [hmevlc] section instead of [DEFAULT].

       start.py is now identical to the HME for Python version; the port
       and datapath are set in config.ini. (If you're upgrading from a
       previous version and have your own, modified config.ini, you
       should copy the [hmeserver] and [hmevlc] sections from the new
       one.)

       It should no longer be necessary to set the datapath under
       Windows, unless your videos are on a different drive from
       HME/VLC. You still can only use shares on one drive at a time,
       unless all the videos in a share require reencoding.

       Paths in config.ini are now validated; shares with invalid paths 
       are skipped.

       Reorganized.

2.4 -- Allow specifying the location of VLC via "vlc=/path/to/vlc" in 
       the DEFAULTS section of config.ini.

       When VLC is missing, don't show items that need it.

       Allow the Advance key to skip to the end/beginning of a menu.

       Remember the position in lower menus as well as higher. This is
       closer to the behavior of the TiVo's built-in menus. They're only
       remembered while the app is running.

       Use images for the menu backgrounds. I liked my squares routine,
       but the TiVo didn't like all those transparent views.

       A little more room for text in menus.

2.3 -- No more leaking text resources.

       For debugging purposes, I'd disabled the 9.4-TiVo-software-only
       test, and forgot to reenable it before releasing 2.2. Not for the
       first time.

2.2 -- Generates fewer views, less cropping in the info bar, and minor
       tweaks to bring it closer to standard TiVo menu behavior.

2.1 -- Support for local file shares.

2.0 -- Now presents itself as one app, generates its own menu, and uses
       config.ini to define streams.

1.3 -- Rearranged to use the HME for Python package unmodified (except 
       for the port number and name in start.py, nee hmeserver.py).

1.2 -- More graceful handling of some error conditions.

       Added C-SPAN and ResearchChannel.

1.1 -- Added fps and samplerate to the VLC parameters (the TiVo can only
       accept certain values for these). Not needed for NASA TV, but for
       some other files/streams.

       The progess bar colors and sounds were not always being updated
       correctly.
