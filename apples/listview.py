import time

import hme

WIPETIME = 0.5

class ListView:
    def __init__(self, app, title, items, pos=0, startpos=0):
        self.selected = None
        self.app = app
        self.sound = app.sound
        self.title = title
        self.items = items
        self.pos = pos
        self.startpos = startpos
        if len(items) < 10:
            self.pagesize = len(items)
        else:
            self.pagesize = 10

    def draw(self):
        self.base = self.app.root.child(visible=False)
        self.titleshadow = self.base.child(68, 50, 508, 62, transparency=0.5)
        self.titlewin = self.base.child(64, 48, 512, 64)
        self.base.set_translation(640, 0)

        self.base.child(64, 112, 576, 320, transparency=0.5, colornum=0)
        self.bar = self.base.child(0, 112, 576, 32, colornum=0xffff00)
        self.bar.child(0, 1, 575, 30, colornum=0xaf)

        self.upwin = self.base.child(570, 100, 12, 12, visible=False,
                                     image='apples/up.png')
        self.downwin = self.base.child(570, 432, 12, 12, visible=False,
                                       image='apples/down.png')

        self.page = [(self.base.child(108, i * 32 + 112, 467, 32),
                      self.base.child(64, i * 32 + 112, 44, 32))
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
        self.upwin.set_visible(self.startpos)
        self.downwin.set_visible(len(self.items) >
                                 self.startpos + self.pagesize)

    def remove(self):
        for line in self.page:
            line[0].remove_resource()
        self.title_clear()
        self.base.remove()

    def title_update(self, title_text):
        self.title_clear()
        hme.Font(self.app, size=48)
        hme.Color(self.app, 0)
        self.titleshadow.set_text(title_text, flags=hme.RSRC_VALIGN_TOP)
        hme.Color(self.app, 0x9f9f00)
        self.titlewin.set_text(title_text, flags=hme.RSRC_VALIGN_TOP)
        hme.Font(self.app)
        hme.Color(self.app)

    def pos_update(self):
        self.bar.set_bounds(ypos=((self.pos - self.startpos) * 32 + 112))

    def down(self, i):
        self.pos += i
        if self.pos >= len(self.items):
            self.pos = len(self.items) - 1
        if self.pos >= (self.startpos + self.pagesize):
            self.startpos += (self.pagesize - 1)
            if self.startpos + self.pagesize > len(self.items):
                self.startpos = len(self.items) - self.pagesize
            self.redraw()
        self.pos_update()

    def up(self, i):
        self.pos -= i
        if self.pos < 0:
            self.pos = 0
        if self.pos < self.startpos:
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
            self.down(1)
        elif code == hme.KEY_UP and self.pos > 0:
            self.sound()
            self.up(1)
        elif code == hme.KEY_CHANNELDOWN and self.pos < len(self.items) - 1:
            self.sound('pagedown')
            self.down(self.pagesize)
        elif code == hme.KEY_CHANNELUP and self.pos > 0:
            self.sound('pageup')
            self.up(self.pagesize)
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
        elif code not in (hme.KEY_VOLUMEUP, hme.KEY_VOLUMEDOWN,
                          hme.KEY_MUTE, hme.KEY_TIVO):
            self.sound('bonk')

    def handle_key_repeat(self, code, rawcode):
        self.handle_key_press(code, rawcode)

    def handle_focus(self, focus):
        if focus:
            self.draw()
            self.pos_update()
            self.base.set_visible()
            if self.selected:
                self.base.set_translation(0, 0)
            else:
                anim = hme.Animation(self.app, WIPETIME, 1)
                self.base.set_translation(0, 0, anim)
                time.sleep(WIPETIME)
            self.title_update(self.title)
        else:
            if not self.selected:
                anim = hme.Animation(self.app, WIPETIME, -1)
                self.title_update('')
                self.bar.remove()
                self.base.set_translation(640, 0, anim)
                time.sleep(WIPETIME)
            self.remove()
