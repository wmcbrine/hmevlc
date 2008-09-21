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

""" HME app """

__author__ = 'William McBrine <wmcbrine@gmail.com>'
__version__ = '2.4'
__license__ = 'GPL'

import os
import time
import urllib
from ConfigParser import SafeConfigParser

import hme
from hmevlc.listview import ListView
from hmevlc.hmevid import VideoStreamer

TITLE = 'HME/VLC'

PASSTHROUGH_EXTS = ('.mpg', '.mp4')
TRANSCODE_EXTS = ('.mov', '.wmv', '.avi', '.asf', '.flv', '.mkv')

MENU_TOP = 0
MENU_STREAMS = 1
MENU_FILES = 2

class Hmevlc(hme.Application):
    def handle_device_info(self, info):
        return
        ver = info.get('version', '')
        if float(ver[:3]) < 9.4:
            self.root.set_text('Sorry, this program is not compatible\n' +
                               'with this TiVo software/hardware version.')
            time.sleep(5)
            self.active = False

    def get_default(self, section, option, default):
        if self.config.has_option(section, option):
            return self.config.get(section, option)
        else:
            return default

    def get_defaultbool(self, section, option, default):
        if self.config.has_option(section, option):
            return self.config.getboolean(section, option)
        else:
            return default

    def handle_active(self):
        self.config = SafeConfigParser()
        self.config.read('config.ini')

        self.positions = {}

        self.have_vlc = vlc.have(self.get_default('DEFAULT', 'vlc', None))
        if self.have_vlc:
            self.exts = PASSTHROUGH_EXTS + TRANSCODE_EXTS
        else:
            self.exts = PASSTHROUGH_EXTS

        self.stream_list = []
        dir_list = []
        for title in sorted(self.config.sections()):
            if self.config.has_option(title, 'url'):
                if (self.have_vlc or
                    not(self.get_defaultbool(title, 'needs_vlc', False))):
                    self.stream_list.append((title,
                        self.get_default(title, 'icon', '')))
            elif self.config.has_option(title, 'dir'):
                path = self.config.get(title, 'dir')
                if os.path.isdir(path):
                    dir_list.append((title, 'hmevlc/folder.png'))
                else:
                    print 'Bad path:', path

        self.in_list = True
        self.filemenus = []

        if self.stream_list:
            dir_list = [('Live Streams', 'hmevlc/folder.png')] + dir_list
        self.top_menu = ListView(self, TITLE, dir_list)
        self.show_top()

    def show_top(self):
        self.root.set_image('hmevlc/red.png')
        self.menu_mode = MENU_TOP
        self.set_focus(self.top_menu)

    def show_streams(self):
        self.root.set_image('hmevlc/blue.png')
        self.set_focus(self.stream_menu)

    def handle_focus_streams(self, focus):
        if self.in_list:
            if focus:
                if self.stream_menu.selected:
                    title = self.stream_menu.selected[1]
                    vid = VideoStreamer(self, title,
                        self.config.get(title, 'url'),
                        self.get_defaultbool(title, 'needs_vlc', False))
                    self.in_list = False
                    self.set_focus(vid)
                else:
                    self.positions['Live Streams'] = (self.stream_menu.pos,
                        self.stream_menu.startpos)
                    self.show_top()
        else:
            if focus:
                self.in_list = True
                self.show_streams()

    def new_menu(self, title, path):
        ld = os.listdir(path)
        dirs = []
        files = []
        for i in ld:
            if os.path.isdir(os.path.join(path, i)):
               dirs.append(i)
            else:
               if os.path.splitext(i)[1].lower() in self.exts:
                   files.append(i)
        dirs.sort()
        files.sort()
        pos, startpos = self.positions.get(path, (0, 0))
        a = ListView(self, title, [(i, 'hmevlc/folder.png') for i in dirs] +
                                  [(i, '') for i in files], pos, startpos)
        a.basepath = path
        self.set_focus(a)
        self.filemenus.append(a)
        self.in_list = True

    def handle_focus_files(self, focus):
        if self.in_list:
            if focus:
                a = self.filemenus[-1]
                if a.selected:
                    newpath = os.path.join(a.basepath, a.selected[1])
                    if os.path.isdir(newpath):
                        self.new_menu(a.selected[1], newpath)
                    else:
                        vlc = (os.path.splitext(newpath)[1].lower()
                               not in PASSTHROUGH_EXTS)
                        if vlc:
                            url = newpath
                        else:
                            base = self.context.server.datapath
                            host = self.context.headers['host']
                            newpath = newpath.replace(base, '', 1)
                            url = 'http://%s/%s' % (host, urllib.quote(newpath))
                        vid = VideoStreamer(self, a.selected[1], url, vlc)
                        self.in_list = False
                        self.set_focus(vid)
                else:
                    self.positions[a.basepath] = (a.pos, a.startpos)
                    self.filemenus.pop()
                    if self.filemenus:
                        self.set_focus(self.filemenus[-1])
                    else:
                        self.show_top()
        else:
            if focus:
                self.root.set_image('hmevlc/green.png')
                self.in_list = True
                self.set_focus(self.filemenus[-1])

    def handle_focus(self, focus):
        if self.menu_mode == MENU_STREAMS:
            self.handle_focus_streams(focus)
        elif self.menu_mode == MENU_FILES:
            self.handle_focus_files(focus)
        else:
            if focus:
                if self.top_menu.selected:
                    title = self.top_menu.selected[1]
                    if title == 'Live Streams':
                        self.menu_mode = MENU_STREAMS
                        pos, startpos = self.positions.get('Live Streams',
                                                           (0, 0))
                        self.stream_menu = ListView(self, 'Live Streams',
                                                    self.stream_list,
                                                    pos, startpos)
                        self.show_streams()
                    else:
                        self.root.set_image('hmevlc/green.png')
                        self.menu_mode = MENU_FILES
                        self.new_menu(title, self.config.get(title, 'dir'))
                else:
                    self.active = False
