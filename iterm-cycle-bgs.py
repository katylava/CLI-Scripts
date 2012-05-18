#!/usr/bin/env python

from appscript import app, its
from splitscreenbgs import get_size_from_image, choose_pix, make_bg, GenerateImageError

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800
INPUT_DIR = "/Users/kyl/Pictures/Wallpapers/InRotation"
OUTPUT_DIR = "/Users/kyl/Pictures/SplitScreenBGs"


class ItermSessionBG:
    tty = None
    num = None
    prefix = None
    session = None
    current = None

    def __init__(self, tty, prefix=None):
        self.tty = tty
        self.num = tty[-2:]
        self.prefix = prefix

        iterm = app('iTerm')
        term = iterm.current_terminal()
        self.session = term.sessions[its.id==tty]
        self.current = self.session.background_image_path()[0]

        if not self.current:
            if not self.prefix:
                raise NotImplementedError('Please provide a prefix')
            else:
                self.set_session_bg() # sets self.current

        self.current_prefix = self.current.split('/')[-1].rpartition('.')[0]
        self.prefix = prefix or self.current_prefix

    def filename(self):
        return '{}.{}'.format(self.prefix, self.num)

    def set_session_bg(self):
        self.current = '{}/{}.jpg'.format(OUTPUT_DIR, self.filename())
        self.session.background_image_path.set(self.current)
        return self.current

    def get_ratio(self):
        size = get_size_from_image(self.prefix, OUTPUT_DIR)
        return [(
            self.prefix,
            float(size[0])/SCREEN_WIDTH,
            float(size[1])/SCREEN_HEIGHT,
        )]

    def change_session_bg(self):
        ratio = self.get_ratio()
        images = choose_pix(INPUT_DIR, SCREEN_WIDTH, SCREEN_HEIGHT, ratio)
        spec = images[self.prefix]

        try:
            im = make_bg(spec['file'], spec['size'])
        except GenerateImageError as e:
            print("\tError generating image: {}".format(e.message))
        else:
            try:
                im.save(self.current)
            except Exception as e:
                print("\tError saving image to {}: {}".format(self.current,
                                                              e.message))


if __name__ == '__main__':
    import os, sys

    fd = sys.stdout.fileno()
    tty = os.ttyname(fd)
    argc = len(sys.argv)
    prefix = None if argc<2 else sys.argv[1]

    bg = ItermSessionBG(tty, prefix)
    bg.change_session_bg()

    # refresh session by resizing text
    iterm = app('System Events').processes['iTerm']
    menu = iterm.menu_bars[0].menus['View'].menu_items
    menu['Make Text Smaller'].click()
    menu['Make Text Bigger'].click()

    print(bg.current)

