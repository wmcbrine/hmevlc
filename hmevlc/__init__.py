# HME/VLC video streamer, v3.6
# Copyright 2010 William McBrine
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
__version__ = '3.6'
__license__ = 'GPL'

import os
import re
import sys
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

GRAPHICS = ('red', 'blue', 'green', 'folder')
GRAPHICS_TEMPLATES = ('apples/%s.png', 'apples/%s-hd.png')
RSS_ICONS = ('icons/rss.png', 'icons/rss-hd.png')
RED, BLUE, GREEN = 0, 1, 2

TAGS = re.compile(r'<.*?>')

BOM = '\xef\xbb\xbf'

def untag(text):
    if text:
        return TAGS.sub('', text).strip()
    else:
        return ''

def pytivo_metadata(full_path):
    metadata = {}
    path, name = os.path.split(full_path)
    for metafile in [os.path.join(path, 'default.txt'), full_path + '.txt',
                     os.path.join(path, '.meta', 'default.txt'),
                     os.path.join(path, '.meta', name) + '.txt']:
        if os.path.exists(metafile):
            for line in file(metafile, 'U'):
                if line.startswith(BOM):
                    line = line[3:]
                if line.strip().startswith('#') or not ':' in line:
                    continue
                key, value = [x.strip() for x in line.split(':', 1)]
                if not key or not value:
                    continue
                try:
                    value = value.decode('utf8')
                except:
                    if sys.platform == 'darwin':
                        value = value.decode('macroman')
                    else:
                        value = value.decode('iso8859-1')
                metadata[key] = value
    return metadata

class Hmevlc(hme.Application):
    def startup(self):
        self.using_vlc = False
        self.hd = False

    def handle_device_info(self, info):
        ver = info.get('version', '')
        if float(ver[:3]) < 9.4:
            self.root.set_text('Sorry, this program is not compatible\n' +
                               'with this TiVo software/hardware version.')
            self.sleep(5)
            self.active = False

    def handle_resolution(self):
        hd = (1280, 720, 1, 1)
        self.hd = hd in self.resolutions
        if self.hd:
            return hd
        else:
            return (640, 480, 1, 1)

    def handle_active(self):
        config = self.context.server.config
        self.positions = {}

        self.graphics = [GRAPHICS_TEMPLATES[self.hd] % item
                         for item in GRAPHICS]
        folder = self.graphics[3]

        self.have_vlc = vlc.have(config)
        self.pass_exts = [x for x in self.context.MIMETYPES
                          if self.context.MIMETYPES[x] in
                          ('video/mpeg', 'video/mp4', 'video/x-tivo-mpeg')]
        if self.have_vlc:
            self.exts = [x for x in self.context.MIMETYPES
                         if self.context.MIMETYPES[x].startswith('video')]
        else:
            self.exts = self.pass_exts

        self.stream_list = []
        self.rss_list = []
        shout_list = []
        dir_list = []
        for title in sorted(config.sections()):
            if config.has_option(title, 'needs_vlc'):
                needs_vlc = config.getboolean(title, 'needs_vlc')
            else:
                needs_vlc = False
            if self.have_vlc or not needs_vlc:
                item = {'title': title}
                item.update(config.items(title))
                item['needs_vlc'] = needs_vlc
                if 'dir' in item:
                    if os.path.isdir(item['dir']):
                        item['func'] = self.new_menu_files
                        if not 'icon' in item:
                            item['icon'] = folder
                        dir_list.append(item)
                    else:
                        self.context.log_message('Bad path: %s', item['dir'])
                elif 'url' in item:
                    item['func'] = self.play_stream
                    self.stream_list.append(item)
                elif ET and 'rss' in item:
                    item['func'] = self.new_menu_rss
                    if not 'icon' in item:
                        item['icon'] = RSS_ICONS[self.hd]
                    self.rss_list.append(item)
                elif ET and 'shout_list' in item:
                    item['func'] = self.top_menu_shoutcast
                    if not 'icon' in item:
                        item['icon'] = folder
                    shout_list.append(item)

        self.in_list = True

        items = []
        if self.stream_list:
            if len(self.stream_list) < 4:
                items += self.stream_list
            else:
                items.append({'title': 'Live Streams', 'icon': folder,
                              'func': self.top_menu_live})
        if self.rss_list:
            if len(self.rss_list) < 4:
                items += self.rss_list
            else:
                items.append({'title': 'RSS Feeds', 'icon': folder,
                              'func': self.top_menu_rss})
        items += shout_list + dir_list

        self.menus = []
        self.background = None
        if len(items) == len(dir_list) == 1:
            self.new_menu_files(dir_list[0])
        else:
            if len(items) == 1:
                if self.stream_list:
                    items = self.stream_list
                elif self.rss_list:
                    items = self.rss_list
            self.push_menu(TITLE, items, RED)

    def redraw(self):
        self.set_focus(self.menus[-1])

    def set_background(self, color=None):
        if color is None:
            color = self.background
        self.root.set_image(self.graphics[color])
        self.background = color

    def play_stream(self, item):
        vid = VideoStreamer(self, item)
        self.in_list = False
        self.set_focus(vid)

    def new_menu_files(self, share):
        path = share['dir']
        needs_vlc = share['needs_vlc']
        dirs, files = [], []
        for i in sorted(os.listdir(unicode(path))):
            item = {'title': i, 'needs_vlc': needs_vlc}
            newpath = os.path.join(path, i)
            if os.path.isdir(newpath):
                item.update({'icon': self.graphics[3], 'dir': newpath,
                             'func': self.new_menu_files})
                dirs.append(item)
            else:
                ext = os.path.splitext(i)[1].lower()
                if ext in self.exts:
                    if ext not in self.pass_exts:
                        item['needs_vlc'] = True
                    item.update({'url': newpath, 'func': self.play_file})
                    files.append(item)
        self.push_menu(share['title'], dirs + files, GREEN, path)

    def play_file(self, s):
        item = {}
        item.update(s)
        url = s['url']
        metadata = pytivo_metadata(url)
        if 'description' in metadata and metadata['description']:
            item['desc'] = metadata['description']
        if not s['needs_vlc']:
            url = url.replace(self.context.server.datapath, '', 1)
            url = 'http://%s/%s' % (self.context.headers['host'],
                                    urllib.quote(url.encode('utf-8')))
            item['url'] = url
        self.play_stream(item)

    def top_menu_live(self, live):
        self.push_menu(live['title'], self.stream_list, BLUE)

    def top_menu_rss(self, rss):
        self.push_menu(rss['title'], self.rss_list, BLUE)

    def top_menu_shoutcast(self, shout_item):
        shout_tune = shout_item['shout_tune']
        needs_vlc = shout_item['needs_vlc']
        feed = urllib.urlopen(shout_item['shout_list'])
        try:
            tree = ET.parse(feed)
        except Exception, msg:
            self.context.log_message('Shoutcast parse - %s', msg)
            self.redraw()
            return
        stations = []
        for station in tree.getroot():
            if station.get('rt') != 'NC17':
                item = {'url': shout_tune + station.get('id'),
                        'needs_vlc': needs_vlc, 'func': self.play_stream}
                name = station.get('name').strip()
                ct = station.get('ct').strip()
                if ct:
                    item.update({'title': ct, 'desc': name})
                else:
                    item['title'] = name
                stations.append(item)
        self.push_menu(shout_item['title'], stations, BLUE)

    def new_menu_rss(self, rss_item):
        needs_vlc = rss_item['needs_vlc']
        feed = urllib.urlopen(rss_item['rss'])
        try:
            tree = ET.parse(feed)
        except Exception, msg:
            self.context.log_message('RSS parse - %s', msg)
            self.redraw()
            return
        items = []
        for item in tree.getiterator('item'):
            enc = item.find('enclosure')
            if enc is not None and enc.get('type', '').startswith('video'):
                items.append({'title': item.findtext('title').strip(),
                              'url': enc.get('url'), 'needs_vlc': needs_vlc,
                              'func': self.play_stream})
                desc = untag(item.findtext('description'))
                if desc:
                    items[-1]['desc'] = desc
        self.push_menu(rss_item['title'], items, BLUE)

    def push_menu(self, title, items, color, path=None):
        if not path:
            path = title
        if self.background != color:
            self.set_background(color)
        pos, startpos = self.positions.get(path, (0, 0))
        menu = ListView(self, title, items, pos, startpos)
        menu.basepath = path
        menu.color = color
        self.menus.append(menu)
        self.set_focus(menu)

    def pop_menu(self):
        menu = self.menus.pop()
        self.positions[menu.basepath] = (menu.pos, menu.startpos)
        if self.menus:
            menu = self.menus[-1]
            if self.background != menu.color:
                self.set_background(menu.color)
            self.set_focus(menu)
        else:
            self.active = False

    def handle_focus(self, focus):
        if focus:
            if self.in_list:
                s = self.menus[-1].selected
                if s:
                    s['func'](s)
                else:
                    self.pop_menu()
            else:
                self.in_list = True
                self.set_background()
                self.redraw()

    def cleanup(self):
        if self.using_vlc:
            vlc.stop()
