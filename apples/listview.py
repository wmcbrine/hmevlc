# Apples and Oranges, v0.4
# Copyright 2009 William McBrine
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You didn't receive a copy of the license with this library because
# you already have dozens of copies, don't you? If not, visit gnu.org.

__author__ = 'William McBrine <wmcbrine@gmail.com>'
__version__ = '0.4'
__license__ = 'LGPL'

""" Apples and Oranges -- ListView

    The ListView class creates a simple, navigable list, in a style
    similar to TiVo's native menus. It's initialized with a title and a
    list of tuples, each tuple containing the text for a line, and an
    optional icon (use None or '' for no icon). The starting selector 
    and list positions can also be given; they default to 0. You may 
    also specify the root window.

    Create the instance, then give it focus via set_focus(). When
    finished, it returns control to the app in the same way; check the
    results in the app's handle_focus(). The "selected" attribute
    contains None if the user backed out of the menu; otherwise it holds
    a tuple of the item number and text selected.

"""

import time

import hme

WIPETIME = 0.5

class ListView:
    def __init__(self, app, title, items, pos=0, startpos=0, root=None):
        self.selected = None
        self.app = app
        self.sound = app.sound
        self.title = title
        self.items = items
        self.pos = pos
        self.startpos = startpos
        if not root:
            root = self.app.root
        self.root = root
        self.w = root.width
        self.h = root.height
        if self.w == 1280:
            self.title_height = 96
            self.bar_height = 48
            self.fsize = 36
            self.icon_width = 66
            self.round_width = 24
            self.round = 'apples/round-hd.png'
            self.inner_offset = 2
        else:
            self.title_height = 64
            self.bar_height = 32
            self.fsize = 24
            self.icon_width = 44
            self.round_width = 17
            self.round = 'apples/round.png'
            self.inner_offset = 1
        size = ((self.h - 2 * hme.SAFE_TITLE_V - self.title_height) /
                self.bar_height)
        if len(items) < size:
            size = len(items)
        self.pagesize = size

    def draw(self):
        stw = hme.SAFE_TITLE_H
        sth = hme.SAFE_TITLE_V
        saw = hme.SAFE_ACTION_H
        sah = hme.SAFE_ACTION_V
        mainw = self.w - 2 * stw
        th = self.title_height
        bh = self.bar_height
        bw = mainw + stw
        starth = th + sth
        endh = self.h - sth
        iconw = self.icon_width

        self.base = self.root.child(visible=False)
        self.titleshadow = self.base.child(stw + 4, sth + 2, mainw - 4,
                                           th - 2, transparency=0.5)
        self.titlewin = self.base.child(stw, sth, mainw, th)
        self.base.set_translation(self.w, 0)
        self.bar = self.base.child(0, starth, bw, bh)
        self.bar.child(width=(bw - self.round_width), colornum=0xffff00)
        self.bar.child(0, self.inner_offset, bw - self.round_width,
                       bh - 2 * self.inner_offset, colornum=0xaf)
        self.bar.child(xpos=(bw - self.round_width), image=self.round)

        self.upwin = self.base.child(bw - 6, starth - 12, 12, 12, visible=False,
                                     image='apples/up.png')
        self.downwin = self.base.child(bw - 6, endh, 12, 12, visible=False,
                                       image='apples/down.png')
        self.page = [(self.base.child(iconw + stw, i * bh + starth,
                                      mainw - iconw - 18, bh),
                      self.base.child(stw, i * bh + starth, iconw, bh))
                     for i in xrange(self.pagesize)]
        self.redraw()

    def title_clear(self):
        self.titleshadow.remove_resource()
        self.titlewin.remove_resource()

    def redraw(self):
        hme.Color(self.app, 0xcfcfcf)
        for i, item in enumerate(self.items[self.startpos:self.startpos +
                                            self.pagesize]):
            self.page[i][0].remove_resource()
            self.page[i][0].set_text(item[0], flags=hme.RSRC_HALIGN_LEFT)
            if item[1]:
                self.page[i][1].set_image(item[1])
            else:
                self.page[i][1].clear_resource()
        hme.Color(self.app)
        self.upwin.set_visible(self.startpos > 0)
        self.downwin.set_visible(len(self.items) >
                                 self.startpos + self.pagesize)

    def remove(self):
        for line in self.page:
            line[0].remove_resource()
        self.title_clear()
        self.base.remove()

    def title_update(self, title_text):
        self.title_clear()
        hme.Font(self.app, size=(self.fsize * 2))
        hme.Color(self.app, 0)
        self.titleshadow.set_text(title_text, flags=hme.RSRC_VALIGN_TOP)
        hme.Color(self.app, 0x9f9f00)
        self.titlewin.set_text(title_text, flags=hme.RSRC_VALIGN_TOP)
        hme.Font(self.app, size=self.fsize)
        hme.Color(self.app)

    def pos_update(self):
        self.bar.set_bounds(ypos=((self.pos - self.startpos) *
                                  self.bar_height + self.title_height + 
                                  hme.SAFE_TITLE_V))

    def down(self):
        self.pos += 1
        if self.pos >= len(self.items):
            self.pos = len(self.items) - 1
        if self.pos >= (self.startpos + self.pagesize):
            self.startpos += (self.pagesize - 1)
            if self.startpos + self.pagesize > len(self.items):
                self.startpos = len(self.items) - self.pagesize
            self.redraw()
        self.pos_update()

    def page_down(self):
        self.pos += (self.pagesize - 1)
        if self.pos >= len(self.items):
            self.pos = len(self.items) - 1
        self.startpos += (self.pagesize - 1)
        if self.startpos + self.pagesize > len(self.items):
            self.startpos = len(self.items) - self.pagesize
        self.redraw()
        self.pos_update()

    def up(self):
        self.pos -= 1
        if self.pos < 0:
            self.pos = 0
        if self.pos < self.startpos:
            self.startpos -= (self.pagesize - 1)
            if self.startpos < 0:
                self.startpos = 0
            self.redraw()
        self.pos_update()

    def page_up(self):
        self.pos -= (self.pagesize - 1)
        if self.pos < 0:
            self.pos = 0
        self.startpos -= (self.pagesize - 1)
        if self.startpos < 0:
            self.startpos = 0
        self.redraw()
        self.pos_update()

    def handle_key_press(self, code, rawcode):
        if code == hme.KEY_LEFT:
            self.sound('left')
            self.selected = None
            self.app.set_focus(self.app)
        elif code == hme.KEY_DOWN and self.pos < len(self.items) - 1:
            self.sound()
            self.down()
        elif code == hme.KEY_UP and self.pos > 0:
            self.sound()
            self.up()
        elif code == hme.KEY_CHANNELDOWN and self.pos < len(self.items) - 1:
            self.sound('pagedown')
            self.page_down()
        elif code == hme.KEY_CHANNELUP and self.pos > 0:
            self.sound('pageup')
            self.page_up()
        elif code == hme.KEY_ADVANCE:
            self.sound('speedup3')
            if self.pos < len(self.items) - 1:
                self.pos = len(self.items) - 1
                self.startpos = len(self.items) - self.pagesize
            else:
                self.pos = 0
                self.startpos = 0
            self.redraw()
            self.pos_update()
        elif code in (hme.KEY_RIGHT, hme.KEY_SELECT, hme.KEY_PLAY):
            self.sound('select')
            if self.items:
                self.selected = (self.pos, self.items[self.pos][0])
            self.app.set_focus(self.app)
        elif code == hme.KEY_TIVO:
            self.title_update(self.title)
        elif code not in (hme.KEY_VOLUMEUP, hme.KEY_VOLUMEDOWN, hme.KEY_MUTE):
            self.sound('bonk')

    def handle_key_repeat(self, code, rawcode):
        self.handle_key_press(code, rawcode)

    def handle_focus(self, focus):
        if focus:
            hme.Font(self.app, size=self.fsize)
            self.draw()
            self.pos_update()
            self.base.set_visible()
            if self.selected:
                self.base.set_translation(0, 0)
                self.title_update(self.title)
            else:
                anim = hme.Animation(self.app, WIPETIME, 1)
                self.base.set_translation(0, 0, anim)
                self.app.send_key(hme.KEY_TIVO, animation=anim)
        else:
            if not self.selected:
                anim = hme.Animation(self.app, WIPETIME, -1)
                self.title_update('')
                self.bar.remove()
                self.base.set_translation(self.w, 0, anim)
                time.sleep(WIPETIME)
            self.remove()
            hme.Font(self.app)
