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

""" Video streamer class """

__author__ = 'William McBrine <wmcbrine@gmail.com>'
__version__ = '2.4'
__license__ = 'GPL'

import time

import hme
from hmevlc import vlc

SPEEDS = [-60, -18, -3, 1, 3, 18, 60]
SOUNDS = ['speedup3', 'speedup2', 'speedup1', 'slowdown1', 'speedup1', 
          'speedup2', 'speedup3']
COLORS = [0x4f4fff, 0x7f7fff, 0x9f9fff, 0xffcfcf, 0xff9f9f, 0xff7f7f, 0xff4f4f]

BWIDTH = 370
BHEIGHT = 32
TGAP = 8
TWIDTH = 144
BSIZE = BWIDTH + TGAP + TWIDTH + 1

BG = 0
BG2 = 0x7f7f7f
FG = 0xffffff

TIMEFORMAT = '%I:%M %p '

class VideoStreamer:
    def __init__(self, app, title, stream_url, needs_vlc=False):
        self.app = app
        self.root = app.root
        self.clear_sent = 0
        self.info_clear_sent = 0
        self.loadwin = None
        self.progbar = None
        self.info = None
        self.stream = None
        self.title = title
        self.stream_url = stream_url
        self.needs_vlc = needs_vlc
        self.sound = app.sound
        self.send_key = app.send_key

    def loadwin_remove(self):
        if self.loadwin:
            self.loadwin.resource.remove()
            self.loadwin.remove()
            self.loadwin = None

    def handle_focus(self, focus):
        if focus:
            self.loadwin = self.root.child(text='Loading %s...' % self.title)
            self.root.set_color(BG)
            host, port = self.app.context.headers['host'].split(':')
            if self.needs_vlc:
                vlc.start(self.stream_url)
                self.stream = hme.Stream(self.app, 'http://%s:%d/' %
                                         (host, vlc.SERVER), 'video/mpeg')
            else:
                self.stream = hme.Stream(self.app, self.stream_url)
            loadback = self.loadwin.child(278, 258, 84, 14, colornum=BG2)
            self.loadbar = loadback.child(2, 2, 10, 10, colornum=FG)
            self.loadbar_anim()
        else:
            self.loadwin_remove()
            if self.progbar:
                self.poswin.resource.remove()
                self.progbar.remove()
            if self.info:
                self.info_title.resource.remove()
                self.info_time.resource.remove()
                self.info.remove()
            if self.stream:
                self.stream.pause()
                self.stream.remove()
            if self.needs_vlc:
                vlc.stop()
            self.root.set_color(BG)

    def handle_error(self, code, text):
        print 'Error', code, text
        print

    def status_update(self):
        if not self.progbar:
            return
        if self.duration:
            width = self.position * BWIDTH / self.duration
        else:
            width = 0
        if 0 <= self.stream.speed < 1:
            self.status.set_color(FG)
        else:
            i = SPEEDS.index(self.stream.speed)
            self.status.set_color(COLORS[i])
        self.status.set_bounds(width=width)
        dur = int(round(float(self.duration) / 1000))
        pos = int(round(float(self.position) / 1000))
        if dur > 3600 or pos > 3600:
            dur = int(round(float(dur) / 60))
            pos = int(round(float(pos) / 60))
        durstr = '%02d:%02d / %02d:%02d' % (pos / 60, pos % 60,
                                            dur / 60, dur % 60)
        if self.poswin.resource:
            self.poswin.resource.remove()
        self.poswin.set_text(durstr, colornum=FG)

    def status_bar(self):
        self.progbar = self.root.child((640 - BSIZE) / 2, 400, BSIZE, BHEIGHT)
        self.progbar.child(colornum=BG).set_transparency(0.5)
        self.status = self.progbar.child(8, 8, 0, 16, colornum=FG)
        self.poswin = self.progbar.child(BWIDTH + TGAP, 0, TWIDTH)
        self.duration = 0
        self.position = 0

    def info_bar(self):
        self.info = self.root.child((640 - BSIZE) / 2, 48, BSIZE, BHEIGHT)
        self.info.child(colornum=BG).set_transparency(0.5)
        self.info_title = self.info.child(width=(self.info.width - 100))
        self.info_title.set_text(' ' + self.title, colornum=FG,
                                 flags=hme.RSRC_HALIGN_LEFT)
        self.info_time = self.info.child()
        self.info_update()

    def speed_sound(self, newspeed):
        if abs(newspeed) >= 1 and not (newspeed == 1 and 
                                       self.stream.speed == 0):
            i = SPEEDS.index(newspeed)
            self.sound(SOUNDS[i])

    def handle_resource_info(self, resource, status, info):
        if self.stream and resource == self.stream.id:
            if (status >= hme.RSRC_STATUS_ERROR or
                status == hme.RSRC_STATUS_CLOSED):
                if self.loadwin:
                    self.loadwin_remove()
                    err = self.root.child(text='Error reading stream')
                    time.sleep(3)
                    err.resource.remove()
                    err.remove()
                    self.app.set_focus(self.app)
                    return
                if self.stream.speed:
                    self.sound('alert')
                self.change_speed(0)
            elif self.loadwin and status == hme.RSRC_STATUS_READY:
                self.loadwin_remove()
                self.loadbar = None
                self.root.set_resource(self.stream)
                self.status_bar()
                self.info_bar()
                self.update_and_clear(1)
            self.duration = int(info['duration'])
            self.position = int(info['position'])
            newspeed = float(info['speed'])
            if newspeed and newspeed != self.stream.speed:
                self.speed_sound(newspeed)
                self.stream.speed = newspeed
            if (status >= hme.RSRC_STATUS_PLAYING and 
                self.progbar and self.progbar.visible):
                self.status_update()

    def update_and_clear(self, speed):
        if speed == 1:
            self.clear_sent += 1
            self.send_key(hme.KEY_TIVO, 1, animtime=4)
        self.status_update()
        if self.progbar:
            self.progbar.set_visible()

    def info_update(self):
        self.info_clear_sent += 1
        self.send_key(hme.KEY_TIVO, 2, animtime=8)
        if self.info:
            if self.info_time.resource:
                self.info_time.resource.remove()
            self.info_time.set_text(time.strftime(TIMEFORMAT), colornum=FG,
                                    flags=hme.RSRC_HALIGN_RIGHT)
            self.info.set_visible()

    def change_speed(self, newspeed):
        self.update_and_clear(newspeed)
        if newspeed != self.stream.speed:
            self.speed_sound(newspeed)
            self.stream.set_speed(newspeed)

    def change_position(self, newpos):
        self.update_and_clear(self.stream.speed)
        if newpos < 0:
            newpos = 0
        elif newpos > self.duration:
            newpos = self.duration
        self.stream.set_position(newpos)
        if self.stream.speed:
            self.sound('select')

    def loadbar_anim(self):
        if self.loadbar:
            if self.loadbar.xpos == 1:
                newx = 71
            else:
                newx = 1
            self.loadbar.set_bounds(xpos=newx, animtime=1)
            self.send_key(hme.KEY_TIVO, 0, animtime=1)

    def handle_key_press(self, code, rawcode):
        if code == hme.KEY_PLAY:
            if self.stream.speed == 1 and self.progbar.visible:
                self.progbar.set_visible(False)
            else:
                self.change_speed(1)
        elif code == hme.KEY_PAUSE:
            self.change_speed(not self.stream.speed)
        elif code == hme.KEY_REVERSE:
            if self.stream.speed:
                i = SPEEDS.index(self.stream.speed) - 1
                if i > -1:
                    self.change_speed(SPEEDS[i])
                else:
                    self.change_speed(1)
            else:
                self.change_position(self.position - 100)
        elif code == hme.KEY_FORWARD:
            if self.stream.speed:
                i = SPEEDS.index(self.stream.speed) + 1
                if i < 7:
                    self.change_speed(SPEEDS[i])
                else:
                    self.change_speed(1)
            else:
                self.change_position(self.position + 100)
        elif code == hme.KEY_REPLAY:
            self.change_position(self.position - 8000)
        elif code == hme.KEY_ADVANCE:
            self.change_position(self.position + 30000)
        elif code == hme.KEY_SLOW:
            self.change_speed(0.125)
        elif code == hme.KEY_CLEAR:
            self.progbar.set_visible(False)
            self.info.set_visible(False)
        elif code == hme.KEY_INFO:
            self.sound('select')
            if self.info.visible:
                self.info.set_visible(False)
            else:
                self.info_update()
        elif code == hme.KEY_TIVO:
            if not rawcode:
                self.loadbar_anim()
            elif rawcode == 1:
                if self.clear_sent:
                    self.clear_sent -= 1
                    if self.stream.speed == 1 and not self.clear_sent:
                        self.progbar.set_visible(False)
            elif rawcode == 2:
                if self.info_clear_sent:
                    self.info_clear_sent -= 1
                    if not self.info_clear_sent:
                        self.info.set_visible(False)
        elif code == hme.KEY_LEFT:
            self.sound('left')
            self.app.set_focus(self.app)
        elif code not in (hme.KEY_VOLUMEUP, hme.KEY_VOLUMEDOWN, hme.KEY_MUTE):
            self.sound('bonk')

    def handle_idle(self, idle):
        if idle and not self.stream.speed:
            if self.needs_vlc:
                vlc.stop()
        return bool(self.stream.speed)
