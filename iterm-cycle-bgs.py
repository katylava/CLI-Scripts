#!/usr/bin/env python

from appscript import app, its
import splitscreenbgs as ss

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 778 # 800 - tab height
INPUT_DIR = "/Users/kyl/Pictures/Wallpapers/InRotation"
OUTPUT_DIR = "/Users/kyl/Pictures/SplitScreenBGs"


class ItermSessionBG:
    tty = None
    num = None
    prefix = None
    session = None
    current = None
    threshhold = None

    def __init__(self, tty, prefix=None):
        self.tty = tty
        self.num = tty[-2:]
        self.prefix = prefix

        iterm = app('iTerm')
        term = iterm.current_terminal()
        self.session = term.sessions[its.id==tty]
        self.current = self.session.background_image_path()[0]

        if not self.current or self.current.__repr__() == 'k.missingvalue':
            if not self.prefix:
                raise NotImplementedError('Please provide a prefix')
            else:
                self.set_session_bg() # sets self.current

        if not self.prefix:
            self.prefix = self.current.split('/')[-1].split('.')[0]

    def filename(self):
        return '{}.{}'.format(self.prefix, self.num)

    def filepath(self):
        return '{}/{}.jpg'.format(OUTPUT_DIR, self.filename())

    def set_session_bg(self, path=None):
        if not path:
            path = self.filepath()
        self.session.background_image_path.set(path)
        return path

    def unset_bg(self):
        self.session.background_image_path.set(u'')

    def change_session_bg(self, filename=None):
        size = ss.get_size_from_image(self.prefix, OUTPUT_DIR)
        pattern = filename and '{{}}/{}'.format(filename) or None
        path = ss.choose_pic(INPUT_DIR, size[0], size[1], pattern=pattern)
        if not path:
            raise Exception("\tNo images in {} match parameters".format(INPUT_DIR))

        try:
            im = ss.make_bg(path, size, self.threshhold)
        except ss.GenerateImageError as e:
            print("\tError generating image: {}".format(e.message))
        else:
            try:
                im.save(self.filepath())
            except Exception as e:
                print("\tError saving image to {}: {}".format(self.filepath(),
                                                              e.message))
            else:
                return (self.set_session_bg(self.filepath()), path)



if __name__ == '__main__':
    import os, sys
    from optparse import OptionParser
    usage = "Usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option('-p', '--prefix')
    parser.add_option('-r', '--reload', action='store_true',
                      help="Set to the last bg for this prefix and this tty")
    parser.add_option('-f', '--filename')
    parser.add_option('-t', '--threshhold', type='int', default=3000,
                      help="Width or height beyond which image should be resized"
                           " instead of cropped")
    parser.add_option('-u', '--unset', action='store_true')
    parser.add_option('-l', '--list', action='store_true',
                      help='List current prefixes in out_dir')
    options, args = parser.parse_args()

    if options.list:
        ss.list_sizes(OUTPUT_DIR)
        exit()

    fd = sys.stdout.fileno()
    tty = os.ttyname(fd)
    if not tty:
        print('Error getting tty')
        exit()

    bg = ItermSessionBG(tty, options.prefix)
    if options.reload:
        exit() # initialization sets to last bg for prefix

    bg.threshhold = options.threshhold
    if options.unset:
        bg.unset_bg()
    else:
        try:
            paths = bg.change_session_bg(filename=options.filename)
            print("Changed {}\nto {}".format(*paths))
        except Exception as e:
            print e.message
        else:
            # refresh screen by resizing text
            iterm = app('System Events').processes['iTerm']
            menu = iterm.menu_bars[0].menus['View'].menu_items
            menu['Make Text Smaller'].click()
            menu['Make Text Bigger'].click()
