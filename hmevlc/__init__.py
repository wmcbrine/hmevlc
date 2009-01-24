# HME/VLC video streamer, v3.2
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
__version__ = '3.2'
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

MENU_TOP = 0
MENU_STREAMS = 1
MENU_FILES = 2

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
        self.pass_exts = [x for x in self.context.MIMETYPES
                          if self.context.MIMETYPES[x] in
                          ('video/mpeg', 'video/mp4', 'video/x-tivo-mpeg')]
        if self.have_vlc:
            self.exts = [x for x in self.context.MIMETYPES
                         if self.context.MIMETYPES[x].startswith('video')]
        else:
            self.exts = self.pass_exts

        if self.hd:
            self.folder = 'apples/folder-hd.png'
        else:
            self.folder = 'apples/folder.png'

        self.stream_list = []
        rss_list = []
        shout_list = []
        dir_list = []
        for title in sorted(self.config.sections()):
            needs_vlc = self.get_defaultbool(title, 'needs_vlc', False)
            if self.have_vlc or not needs_vlc:
                item = {'title': title, 'needs_vlc': needs_vlc}
                icon = self.get_default(title, 'icon', '')
                if icon:
                    item['icon'] = icon
                if self.config.has_option(title, 'dir'):
                    item['func'] = self.top_menu_files
                    path = self.config.get(title, 'dir')
                    if os.path.isdir(path):
                        if not icon in item:
                            item['icon'] = self.folder
                        item['dir'] = path
                        dir_list.append(item)
                    else:
                        print 'Bad path:', path
                elif self.config.has_option(title, 'url'):
                    item['url'] = self.config.get(title, 'url')
                    self.stream_list.append(item)
                elif ET and self.config.has_option(title, 'rss'):
                    item['rss'] = self.config.get(title, 'rss')
                    item['func'] = self.top_menu_rss
                    if not icon in item:
                        item['icon'] = 'icons/rss.png'
                    rss_list.append(item)
                elif ET and self.config.has_option(title, 'shout_list'):
                    item['shout_list'] = self.config.get(title, 'shout_list')
                    item['shout_tune'] = self.config.get(title, 'shout_tune')
                    item['func'] = self.top_menu_shoutcast
                    if not icon in item:
                        item['icon'] = self.folder
                    shout_list.append(item)

        self.in_list = True

        items = []
        if self.stream_list:
            items.append({'title': 'Live Streams', 'icon': self.folder,
                          'func': self.top_menu_live})
        items += rss_list + shout_list + dir_list

        self.menus = [ListView(self, TITLE, items)]
        self.show_top()

    def show_top(self):
        self.root.set_image(self.graphics[0])
        self.menu_mode = MENU_TOP
        self.set_focus(self.menus[0])

    def show_streams(self):
        self.root.set_image(self.graphics[1])
        self.set_focus(self.stream_menu)

    def handle_focus_streams(self):
        if self.in_list:
            s = self.stream_menu.selected
            if s:
                vid = VideoStreamer(self, s['title'], s['url'],
                                    s['needs_vlc'])
                self.in_list = False
                self.set_focus(vid)
            else:
                self.positions[self.stream_menu.title] = (
                    self.stream_menu.pos, self.stream_menu.startpos)
                self.show_top()
        else:
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
        a = ListView(self, title, [{'title': i, 'icon': self.folder}
                                   for i in dirs] +
                                  [{'title': i} for i in files], pos, startpos)
        a.basepath = path
        self.set_focus(a)
        self.menus.append(a)
        self.in_list = True

    def handle_focus_files(self):
        if self.in_list:
            a = self.menus[-1]
            if a.selected:
                title = a.selected['title']
                newpath = os.path.join(a.basepath, title)
                if os.path.isdir(newpath):
                    self.new_menu(title, newpath)
                else:
                    need_vlc = (self.files_need_vlc or
                                os.path.splitext(newpath)[1].lower()
                                not in self.pass_exts)
                    if need_vlc:
                        url = newpath
                    else:
                        base = self.context.server.datapath
                        host = self.context.headers['host']
                        newpath = newpath.replace(base, '', 1)
                        url = 'http://%s/%s' % (host, urllib.quote(newpath))
                    vid = VideoStreamer(self, title, url, need_vlc)
                    self.in_list = False
                    self.set_focus(vid)
            else:
                self.positions[a.basepath] = (a.pos, a.startpos)
                self.menus.pop()
                if len(self.menus) > 1:
                    self.set_focus(self.menus[-1])
                else:
                    self.show_top()
        else:
            self.root.set_image(self.graphics[2])
            self.in_list = True
            self.set_focus(self.menus[-1])

    def top_menu_live(self, live):
        self.menu_mode = MENU_STREAMS
        title = live['title']
        pos, startpos = self.positions.get(title, (0, 0))
        self.stream_menu = ListView(self, title,
                                    self.stream_list, pos, startpos)
        self.show_streams()

    def top_menu_shoutcast(self, shout_item):
        shout_title = shout_item['title']
        shout_tune = shout_item['shout_tune']
        needs_vlc = shout_item['needs_vlc']
        feed = urllib.urlopen(shout_item['shout_list'])
        try:
            tree = ET.parse(feed)
        except Exception, msg:
            print msg
            self.show_top()
            return
        stations = []
        for station in tree.getroot():
            if station.get('rt') != 'NC17':
                title = station.get('ct').strip()
                if not title:
                    title = station.get('name').strip()
                stations.append({'title': title, 'url': shout_tune +
                                 station.get('id'), 'needs_vlc': needs_vlc})
        self.menu_mode = MENU_STREAMS
        pos, startpos = self.positions.get(shout_title, (0, 0))
        self.stream_menu = ListView(self, shout_title, stations, pos, startpos)
        self.show_streams()

    def top_menu_rss(self, rss_item):
        rss_title = rss_item['title']
        needs_vlc = rss_item['needs_vlc']
        feed = urllib.urlopen(rss_item['rss'])
        try:
            tree = ET.parse(feed)
        except Exception, msg:
            print msg
            self.show_top()
            return
        items = []
        for item in tree.getiterator('item'):
            enc = item.find('enclosure')
            if enc is not None and enc.get('type').startswith('video'):
                items.append({'title': item.findtext('title').strip(),
                              'url': enc.get('url'), 'needs_vlc': needs_vlc})
        self.menu_mode = MENU_STREAMS
        pos, startpos = self.positions.get(rss_title, (0, 0))
        self.stream_menu = ListView(self, rss_title, items, pos, startpos)
        self.show_streams()

    def top_menu_files(self, share):
        self.root.set_image(self.graphics[2])
        self.menu_mode = MENU_FILES
        self.files_need_vlc = share['needs_vlc']
        self.new_menu(share['title'], share['dir'])

    def handle_focus(self, focus):
        if focus:
            if self.menu_mode == MENU_STREAMS:
                self.handle_focus_streams()
            elif self.menu_mode == MENU_FILES:
                self.handle_focus_files()
            else:
                s = self.menus[-1].selected
                if s:
                    s['func'](s)
                else:
                    self.active = False

    def cleanup(self):
        if self.using_vlc:
            vlc.stop()
