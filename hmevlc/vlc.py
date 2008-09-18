# HME/VLC video streamer, v2.4
# Copyright 2008 William McBrine
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2.0 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You didn't receive a copy of the license with this program because 
# you already have dozens of copies, don't you? If not, visit gnu.org.

""" VLC launcher """

__author__ = 'William McBrine <wmcbrine@gmail.com>'
__version__ = '2.4'
__license__ = 'GPL'

import os
import subprocess
import sys
import time

SERVER = 9044     # Port for VLC to use to serve video

VCODEC = 'mp1v'
ACODEC = 'mpga'
VBITRATE = 2048
PARAMS = '#transcode{vcodec=%(VCODEC)s,vb=%(VBITRATE)d,' + \
         'acodec=%(ACODEC)s,audio-sync,samplerate=44100,fps=29.97}:' + \
         'std{access=http,dst=:%(SERVER)d,mux=ps}'

# Default locations for VLC under Windows, Mac OS X and Linux.

if sys.platform == 'win32':
    vlcpath = r'C:\Program Files\VideoLAN\VLC\vlc.exe'
elif sys.platform == 'darwin':
    vlcpath = '/Applications/VLC.app/Contents/MacOS/clivlc'
else:
    vlcpath = '/usr/bin/vlc'

client_count = 0
pid = -1

def have(path=None):
    """ Check if VLC is really there; allow setting a non-default path. """
    global vlcpath
    if path:
        vlcpath = path
    return os.path.isfile(vlcpath)

def start(url):
    """ Increment the client count, and start VLC if this is the first
        client.
    """

    global client_count, pid
    client_count += 1
    if client_count == 1:
        pid = subprocess.Popen([vlcpath, url, '-I', 'dummy', '-V', 'dummy',
                                '--sout', PARAMS % globals()]).pid
        # Give VLC a little time to start up before the request.
        time.sleep(2)

def stop():
    """ Decrement the client count, and stop VLC if this was the last
        client.
    """

    global client_count, pid
    if client_count:
        client_count -= 1
        if not client_count:
            if sys.platform == 'win32':
                import ctypes
                handle = ctypes.windll.kernel32.OpenProcess(1, False, pid)
                ctypes.windll.kernel32.TerminateProcess(handle, -1)
                ctypes.windll.kernel32.CloseHandle(handle)
            else:
                import os
                import signal
                os.kill(pid, signal.SIGINT)
