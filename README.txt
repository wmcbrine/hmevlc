HME/VLC video streamer, v3.6
by William McBrine <wmcbrine@gmail.com>
July 3, 2010

A simple streaming HME server for the TiVo Series 3+.

Uses ports 9043 and 9044. Tested on Ubuntu Linux 8.04 through 10.04, Mac 
OS X 10.4, and Windows XP.

Requirements:

- TiVo S3, HD or Premiere with 9.4 or later software

- Python -- 2.x only (2.6.x recommended)
  http://python.org/

- VLC (0.8.6 recommended)
  http://www.videolan.org/

Use:

- Unzip
- (Optional) Edit config.ini to point to your files
- Run start.py
- Go to the Music, Photos and Showcases menu on your TiVo

Stop:

- Ctrl-C on Linux or Mac; close the window on Windows. (Ctrl-C does an
  orderly shutdown that removes the app from the menu, but unfortunately
  this doesn't work in Windows.)

More info:

Streams can require VLC to reencode/rebroadcast them, or not. For the 
TiVo to use a stream directly, without VLC, the stream must be MPEG-1, 
MPEG-2 or MPEG-4 h.264, and served via http. Entries for new streams, 
shares, RSS feeds or Shoutcast sources can be created in config.ini.

Only one instance of VLC will be run at a time, but it can support 
multiple TiVos watching the same stream, with little additional 
overhead. However, two different TiVos can't simultaneously watch two 
different streams if they both require VLC.

VLC 0.9 through early 1.x was broken for HME/VLC's purposes.

Changes:

3.6 -- The latest versions of VLC finally work again, _if_ the frame
       rate is set to 30 (instead of 29.97) and the codec to mp2v
       (instead of mp1v). Reported by "Allanon".

       Now based on HME for Python version 0.18, which includes e.g.
       various fixes for Zeroconf.

       Support for non-ASCII characters in filenames and description
       text.

       The new HD UI on the TiVo Premiere requires RGB icons; use a
       standard-def RSS icon when appropriate.

       Encode audio at 48 KHz instead of 44.1; default video bitrate is
       now 4 Mbps instead of 2.

       Some broken feeds have enclosures with no types.

       Purged some streams and feeds that no longer work, including
       C-SPAN.

3.5 -- Descriptions for Shoutcast, based on the "name" field. This is
       actually backwards -- "name" should be the title, and "ct" the
       description -- but the way the name field is abused, this is the
       only way that makes sense.

       Support for pyTivo .txt files. Currently only the description is
       used.

       Retry with VLC (or show the error message) from handle_error() as
       well as handle_resource_info().

       Tweak the gap between the title and the description -- now six
       lines fit the info window neatly.

       If the only items are either live streams or RSS feeds, skip
       their folders. (This is similar to what's done for files, but
       different -- the top-level menu retains its name and background
       color.)

3.4 -- No more idle timeout during paused video.

       If live streams or RSS feeds are three or fewer items each, show
       the items in the top-level menu instead of a folder; also, if
       only one item would appear in the top-level menu, and it's a
       directory, then show the directory's contents instead.

       Display description text in the info view. Currently this is only
       automatic for RSS items, but you can set it for live streams if
       you like, by adding a "desc=whatever" line.

       More internal reorganization.

3.3 -- Added support for "needs_vlc" in file shares. Normally, the
       extension of the file is used to determine whether VLC should be 
       used; and if playback fails without it, it's retried with VLC. 
       But some files in ostensibly compatible formats don't play, but 
       don't give an error, either, so HME/VLC doesn't know to retry 
       them. Setting "needs_vlc=True" in config.ini for the share will 
       force the use of VLC even for these not-so-compatible files.

       RSS Feeds are now kept in a separate top-level folder.

       Slightly better error reporting/logging.

       Internal reorganization.

3.2 -- Files with the extensions ".tivo", ".m4v", ".mpeg", ".vob", and
       ".m2v" are now passed through without reencoding (in addition to
       the old ones ".mpg" and ".mp4"). The supported extension list is
       now derived from the list of MIME types in start.py.

       Skip items in RSS feeds with no enclosures, or with enclosures 
       not of type video, since some feeds include mixed media.

3.1 -- Use HD menus when possible.

       Wrap text in the "Loading..." screen.

       Separate RSS icon.

3.0 -- Support for iTunes-style RSS feeds, and Shoutcast TV. See the
       included config.ini for configuration examples. Mostly due to
       Jeff Mossontte, aka "Allanon".

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

       The progress bar colors and sounds were not always being updated
       correctly.
