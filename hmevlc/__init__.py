# HME/VLC video streamer, v3.1
# Copyright 2009 William McBrine
# Contributions by Jeff Mossontte
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
__version__ = '3.1'
__license__ = 'GPL'

import os
import time
import urllib
try:
    from xml.etree import ElementTree as ET
except ImportError:
    try:
        from elementtree import ElementTree as ET
    except ImportError:
        ET = None

import hme
from hmevlc import vlc
from apples.listview import ListView
from hmevlc.hmevid import VideoStreamer

TITLE = 'HME/VLC'

GRAPHICS = ('red', 'blue', 'green')
GRAPHICS_TEMPLATES = ('apples/%s.png', 'apples/%s-hd.png')

PASSTHROUGH_EXTS = ('.mpg', '.mp4')
TRANSCODE_EXTS = ('.mov', '.wmv', '.avi', '.asf',
                  '.flv', '.mkv', '.vob', '.m4v')

MENU_TOP = 0
MENU_STREAMS = 1
MENU_FILES = 2
MENU_RSS = 3
MENU_SHOUTCAST = 4

class Hmevlc(hme.Application):
    def startup(self):
        self.using_vlc = False
        self.hd = False

    def handle_device_info(self, info):
        ver = info.get('version', '')
        if float(ver[:3]) < 9.4:
            self.root.set_text('Sorry, this program is not compatible\n' +
                               'with this TiVo software/hardware version.')
            time.sleep(5)
            self.active = False

    def handle_resolution(self):
        hd = (1280, 720, 1, 1)
        self.hd = hd in self.resolutions
        if self.hd:
            return hd
        else:
            return (640, 480, 1, 1)

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
        self.config = self.context.server.config
        self.positions = {}

        self.graphics = [GRAPHICS_TEMPLATES[self.hd] % item
                         for item in GRAPHICS]

        self.have_vlc = vlc.have(self.config)
        if self.have_vlc:
            self.exts = PASSTHROUGH_EXTS + TRANSCODE_EXTS
        else:
            self.exts = PASSTHROUGH_EXTS

        if self.hd:
            self.folder = 'apples/folder-hd.png'
        else:
            self.folder = 'apples/folder.png'

        self.stream_list = []
        rss_list = []
        shout_list = []
        dir_list = []
        for title in sorted(self.config.sections()):
            if self.config.has_option(title, 'dir'):
                path = self.config.get(title, 'dir')
                if os.path.isdir(path):
                    dir_list.append((title, self.folder))
                else:
                    print 'Bad path:', path
            elif (self.have_vlc or
                  not self.get_defaultbool(title, 'needs_vlc', False)):
                if self.config.has_option(title, 'url'):
                    self.stream_list.append((title,
                        self.get_default(title, 'icon', '')))
                elif ET and self.config.has_option(title, 'rss'):
                    rss_list.append((title,
                        self.get_default(title, 'icon', 'icons/rss.png')))
                elif ET and self.config.has_option(title, 'shout_list'):
                    shout_list.append((title,
                        self.get_default(title, 'icon', self.folder)))

        self.in_list = True
        self.filemenus = []

        items = []
        if self.stream_list:
            items.append(('Live Streams', self.folder))
        items += rss_list + shout_list + dir_list

        self.rss_list = [x[0] for x in rss_list]
        self.shout_list = [x[0] for x in shout_list]

        self.top_menu = ListView(self, TITLE, items)
        self.show_top()

    def show_top(self):
        self.root.set_image(self.graphics[0])
        self.menu_mode = MENU_TOP
        self.set_focus(self.top_menu)

    def show_streams(self):
        self.root.set_image(self.graphics[1])
        self.set_focus(self.stream_menu)

    def live_vid(self, title):
        return VideoStreamer(self, title, self.config.get(title, 'url'),
                             self.get_defaultbool(title, 'needs_vlc', False))

    def shout_vid(self, title):
        return VideoStreamer(self, title,
            self.config.get(self.stream_menu.title, 'shout_tune') +
            self.shout_items[self.stream_menu.selected[0]],
            self.get_defaultbool(self.stream_menu.title, 'needs_vlc', False))

    def rss_vid(self, title):
        return VideoStreamer(self, title,
            self.rss_items[self.stream_menu.selected[0]],
            self.get_defaultbool(self.stream_menu.title, 'needs_vlc', False))

    def handle_focus_streams(self, focus, func):
        if self.in_list:
            if focus:
                if self.stream_menu.selected:
                    title = self.stream_menu.selected[1]
                    vid = func(title)
                    self.in_list = False
                    self.set_focus(vid)
                else:
                    self.positions[self.stream_menu.title] = (
                        self.stream_menu.pos, self.stream_menu.startpos)
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
        a = ListView(self, title, [(i, self.folder) for i in dirs] +
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
                        need_vlc = (os.path.splitext(newpath)[1].lower()
                                    not in PASSTHROUGH_EXTS)
                        if need_vlc:
                            url = newpath
                        else:
                            base = self.context.server.datapath
                            host = self.context.headers['host']
                            newpath = newpath.replace(base, '', 1)
                            url = 'http://%s/%s' % (host, urllib.quote(newpath))
                        vid = VideoStreamer(self, a.selected[1], url, need_vlc)
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
                self.root.set_image(self.graphics[2])
                self.in_list = True
                self.set_focus(self.filemenus[-1])

    def handle_top_menu_streams(self):
        self.menu_mode = MENU_STREAMS
        pos, startpos = self.positions.get('Live Streams', (0, 0))
        self.stream_menu = ListView(self, 'Live Streams',
                                    self.stream_list, pos, startpos)
        self.show_streams()

    def handle_top_menu_shoutcast(self, shout_title):
        shout_url = self.config.get(shout_title, 'shout_list')
        feed = urllib.urlopen(shout_url)
        try:
            tree = ET.parse(feed)
        except Exception, msg:
            print msg
            self.show_top()
            return
        stations, ids = [], []
        for station in tree.getroot():
            if station.get('rt') != 'NC17':
                title = station.get('ct').strip()
                if not title:
                    title = station.get('name').strip()
                id = station.get('id')
                stations.append((title, ''))
                ids.append(id)
        self.menu_mode = MENU_SHOUTCAST
        self.shout_items = ids
        pos, startpos = self.positions.get(shout_title, (0, 0))
        self.stream_menu = ListView(self, shout_title, stations, pos, startpos)
        self.show_streams()

    def handle_top_menu_rss(self, rss_title):
        rss_url = self.config.get(rss_title, 'rss')
        feed = urllib.urlopen(rss_url)
        try:
            tree = ET.parse(feed)
        except Exception, msg:
            print msg
            self.show_top()
            return
        titles, urls = [], []
        for item in tree.getiterator('item'):
            title = item.find('title').text.strip()
            url = item.find('enclosure').get('url')
            titles.append((title, ''))
            urls.append(url)
        self.menu_mode = MENU_RSS
        self.rss_items = urls
        pos, startpos = self.positions.get(rss_title, (0, 0))
        self.stream_menu = ListView(self, rss_title, titles, pos, startpos)
        self.show_streams()

    def handle_focus(self, focus):
        if self.menu_mode == MENU_STREAMS:
            self.handle_focus_streams(focus, self.live_vid)
        elif self.menu_mode == MENU_RSS:
            self.handle_focus_streams(focus, self.rss_vid)
        elif self.menu_mode == MENU_SHOUTCAST:
            self.handle_focus_streams(focus, self.shout_vid)
        elif self.menu_mode == MENU_FILES:
            self.handle_focus_files(focus)
        else:
            if focus:
                if self.top_menu.selected:
                    title = self.top_menu.selected[1]
                    if title == 'Live Streams':
                        self.handle_top_menu_streams()
                    elif title in self.rss_list:
                        self.handle_top_menu_rss(title)
                    elif title in self.shout_list:
                        self.handle_top_menu_shoutcast(title)
                    else:
                        self.root.set_image(self.graphics[2])
                        self.menu_mode = MENU_FILES
                        self.new_menu(title, self.config.get(title, 'dir'))
                else:
                    self.active = False

    def cleanup(self):
        if self.using_vlc:
            vlc.stop()
