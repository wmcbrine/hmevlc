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
        self.rss_list = []
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
                    item['func'] = self.handle_focus_streams
                    self.stream_list.append(item)
                elif ET and self.config.has_option(title, 'rss'):
                    item['rss'] = self.config.get(title, 'rss')
                    item['func'] = self.new_menu_rss
                    if not icon in item:
                        item['icon'] = 'icons/rss.png'
                    self.rss_list.append(item)
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
        if self.rss_list:
            items.append({'title': 'RSS Feeds', 'icon': self.folder,
                          'func': self.top_menu_rss})
        items += shout_list + dir_list

        self.menus = []
        self.background_red()
        self.push_menu(TITLE, items)

    def background_red(self):
        self.root.set_image(self.graphics[0])

    def background_blue(self):
        self.root.set_image(self.graphics[1])

    def background_green(self):
        self.root.set_image(self.graphics[2])

    def handle_focus_streams(self, s):
        if self.in_list:
            vid = VideoStreamer(self, s['title'], s['url'],
                                s['needs_vlc'])
            self.in_list = False
            self.set_focus(vid)
        else:
            self.in_list = True
            self.background_blue()
            self.set_focus(self.menus[-1])

    def new_menu_files(self, title, path):
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
        self.push_menu(title, [{'title': i, 'icon': self.folder,
                                'func': self.handle_focus_files}
                               for i in dirs] +
                              [{'title': i,
                                'func': self.handle_focus_files}
                               for i in files], path)
        self.in_list = True

    def handle_focus_files(self, s):
        if self.in_list:
            a = self.menus[-1]
            title = s['title']
            newpath = os.path.join(a.basepath, title)
            if os.path.isdir(newpath):
                self.new_menu_files(title, newpath)
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
            self.background_green()
            self.in_list = True
            self.set_focus(self.menus[-1])

    def top_menu_live(self, live):
        title = live['title']
        self.background_blue()
        self.push_menu(title, self.stream_list)

    def top_menu_rss(self, rss):
        title = rss['title']
        self.background_blue()
        self.push_menu(title, self.rss_list)

    def top_menu_shoutcast(self, shout_item):
        shout_title = shout_item['title']
        shout_tune = shout_item['shout_tune']
        needs_vlc = shout_item['needs_vlc']
        feed = urllib.urlopen(shout_item['shout_list'])
        try:
            tree = ET.parse(feed)
        except Exception, msg:
            print msg
            self.set_focus(self.menus[-1])
            return
        stations = []
        for station in tree.getroot():
            if station.get('rt') != 'NC17':
                title = station.get('ct').strip()
                if not title:
                    title = station.get('name').strip()
                stations.append({'title': title, 'url': shout_tune +
                                 station.get('id'), 'needs_vlc': needs_vlc,
                                 'func': self.handle_focus_streams})
        self.background_blue()
        self.push_menu(shout_title, stations)

    def new_menu_rss(self, rss_item):
        rss_title = rss_item['title']
        needs_vlc = rss_item['needs_vlc']
        feed = urllib.urlopen(rss_item['rss'])
        try:
            tree = ET.parse(feed)
        except Exception, msg:
            print msg
            self.set_focus(self.menus[-1])
            return
        items = []
        for item in tree.getiterator('item'):
            enc = item.find('enclosure')
            if enc is not None and enc.get('type').startswith('video'):
                items.append({'title': item.findtext('title').strip(),
                              'url': enc.get('url'), 'needs_vlc': needs_vlc,
                              'func': self.handle_focus_streams})
        self.background_blue()
        self.push_menu(rss_title, items)

    def top_menu_files(self, share):
        self.background_green()
        self.files_need_vlc = share['needs_vlc']
        self.new_menu_files(share['title'], share['dir'])

    def push_menu(self, title, items, path=None):
        if not path:
            path = title
        pos, startpos = self.positions.get(path, (0, 0))
        menu = ListView(self, title, items, pos, startpos)
        menu.basepath = path
        self.menus.append(menu)
        self.set_focus(menu)

    def pop_menu(self):
        menu = self.menus[-1]
        self.positions[menu.basepath] = (menu.pos, menu.startpos)
        self.menus.pop()
        if self.menus:
            if len(self.menus) == 1:
                self.background_red()
            self.set_focus(self.menus[-1])
        else:
            self.active = False

    def handle_focus(self, focus):
        if focus:
            s = self.menus[-1].selected
            if s:
                s['func'](s)
            else:
                self.pop_menu()

    def cleanup(self):
        if self.using_vlc:
            vlc.stop()
