# HME/VLC video streamer, v2.7
# Copyright 2009 William McBrine
# Contributions by "Allanon"
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
__version__ = '2.7'
__license__ = 'GPL'

import os
import time
import urllib
from xml.etree import ElementTree as ET

import hme
from hmevlc import vlc
from apples.listview import ListView
from hmevlc.hmevid import VideoStreamer

TITLE = 'HME/VLC'

PASSTHROUGH_EXTS = ('.mpg', '.mp4')
TRANSCODE_EXTS = ('.mov', '.wmv', '.avi', '.asf',
                  '.flv', '.mkv', '.vob', '.m4v')

MENU_TOP = 0
MENU_STREAMS = 1
MENU_FILES = 2
MENU_RSS = 3
MENU_SHOUTCASTTV = 4

class Hmevlc(hme.Application):
    def startup(self):
        self.using_vlc = False

    def handle_device_info(self, info):
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
        self.config = self.context.server.config
        self.positions = {}

        self.have_vlc = vlc.have(self.config)
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
                    dir_list.append((title, 'apples/folder.png'))
                else:
                    print 'Bad path:', path

        self.in_list = True
        self.filemenus = []

        if self.stream_list:
            dir_list = [('Live Streams', 'apples/folder.png')] + dir_list
        dir_list += [('ShoutCast TV', 'apples/folder.png'),
                     ('Archive Classic Movies', 'apples/folder.png'),
                     ('TED Talks', 'apples/folder.png'),
                     ('Tekzilla', 'apples/folder.png')]

        self.top_menu = ListView(self, TITLE, dir_list)
        self.show_top()

    def show_top(self):
        self.root.set_image('apples/red.png')
        self.menu_mode = MENU_TOP
        self.set_focus(self.top_menu)

    def show_streams(self):
        self.root.set_image('apples/blue.png')
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
                    self.positions[self.stream_menu.title] = (
                        self.stream_menu.pos, self.stream_menu.startpos)
                    self.show_top()
        else:
            if focus:
                self.in_list = True
                self.show_streams()

    def handle_focus_shoutcasttv(self, focus):
        if self.in_list:
            if focus:
                if self.stream_menu.selected:
                    title = self.stream_menu.selected[1]
                    vid = VideoStreamer(self, title,
                        "http://www.shoutcast.com/sbin/tunein-tvstation.pls?id=" +
                        self.shoutcast_ID[self.stream_menu.selected[0]], True)
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

    def handle_focus_rss(self, focus):
        if self.in_list:
            if focus:
                if self.stream_menu.selected:
                    title = self.stream_menu.selected[1]
                    vid = VideoStreamer(self, title,
                        self.rss_url[self.stream_menu.selected[0]], False)
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
        a = ListView(self, title, [(i, 'apples/folder.png') for i in dirs] +
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
                self.root.set_image('apples/green.png')
                self.in_list = True
                self.set_focus(self.filemenus[-1])

    def handle_top_menu_streams(self):
        self.menu_mode = MENU_STREAMS
        pos, startpos = self.positions.get('Live Streams', (0, 0))
        self.stream_menu = ListView(self, 'Live Streams',
                                    self.stream_list,
                                    pos, startpos)
        self.show_streams()

    def handle_top_menu_shoutcasttv(self):
        feed = urllib.urlopen("http://www.shoutcast.com/sbin/newtvlister.phtml")
        tree = ET.parse(feed)
        self.shoutcast_list = []
        self.shoutcast_ID = []
        for station in tree.getroot():
            if station.get('rt') != 'NC17':
                title = station.get('ct')
                if not title:
                    title = station.get('name')
                id = station.get('id')
                self.shoutcast_list.append((title, ''))
                self.shoutcast_ID.append(id)
        self.menu_mode = MENU_SHOUTCASTTV
        pos, startpos = self.positions.get('ShoutCast TV', (0, 0))
        self.stream_menu = ListView(self, 'ShoutCast TV', self.shoutcast_list,
                                    pos, startpos)
        self.show_streams()

    def rss_parse(self, rss_url, rss_title):
        feed = urllib.urlopen(rss_url)
        tree = ET.parse(feed)
        titles, urls = [], []
        for item in tree.getiterator('item'):
            title = item.find('title').text
            url = item.find('enclosure').get('url')
            titles.append((title, ''))
            urls.append(url)
        self.menu_mode = MENU_RSS
        pos, startpos = self.positions.get(rss_title, (0, 0))
        self.stream_menu = ListView(self, rss_title, titles, pos, startpos)
        self.show_streams()
        return urls

    def handle_top_menu_acm(self):
        self.rss_url = self.rss_parse(
            'http://www.archiveclassicmovies.com/acm.rss',
            'Archive Classic Movies')

    def handle_top_menu_ted(self):
        self.rss_url = self.rss_parse(
            'http://feeds.feedburner.com/tedtalks_video',
            'TED Talks')

    def handle_top_menu_tekzilla(self):
        self.rss_url = self.rss_parse(
            'http://revision3.com/tekzilla/feed/quicktime-high-definition/',
            'Tekzilla')

    def handle_focus(self, focus):
        if self.menu_mode == MENU_STREAMS:
            self.handle_focus_streams(focus)
        elif self.menu_mode == MENU_SHOUTCASTTV:
            self.handle_focus_shoutcasttv(focus)
        elif self.menu_mode == MENU_RSS:
            self.handle_focus_rss(focus)
        elif self.menu_mode == MENU_FILES:
            self.handle_focus_files(focus)
        else:
            if focus:
                if self.top_menu.selected:
                    title = self.top_menu.selected[1]
                    if title == 'Live Streams':
                        self.handle_top_menu_streams()
                    elif title == 'ShoutCast TV':
                        self.handle_top_menu_shoutcasttv()
                    elif title == 'Archive Classic Movies':
                        self.handle_top_menu_acm()
                    elif title == 'TED Talks':
                        self.handle_top_menu_ted()
                    elif title == 'Tekzilla':
                        self.handle_top_menu_tekzilla()
                    else:
                        self.root.set_image('apples/green.png')
                        self.menu_mode = MENU_FILES
                        self.new_menu(title, self.config.get(title, 'dir'))
                else:
                    self.active = False

    def cleanup(self):
        if self.using_vlc:
            vlc.stop()
