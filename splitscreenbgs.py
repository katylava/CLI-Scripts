#!/usr/bin/env python

from datetime import datetime
from shutil import move
from random import shuffle, randrange
from glob import glob
from PIL import Image

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800

def make_bg(file, size, resize_threshhold=3000):
    im = Image.open(file)
    orient = 'wide' if size[0] > size[1] else 'tall'

    # fit to width (or height if target is tall) before cropping
    if im.size[0] >= resize_threshhold or im.size[1] >= resize_threshhold:
        if orient == 'wide':
            ratio = float(size[0])/im.size[0]
            new_size = (size[0], int(ratio*im.size[1]))
        else:
            ratio = float(size[1])/im.size[1]
            new_size = (int(ratio*im.size[0]), size[1])
        im = im.resize(new_size, Image.ANTIALIAS)

    #crop
    width_diff = im.size[0] - size[0]
    height_diff = im.size[1] - size[1]
    if width_diff or height_diff:
        topleft = (0,0) if not width_diff else (
            randrange(0, im.size[0] - size[0]),
            randrange(0, im.size[1] - size[1]),
        )
        bottomright = (
            topleft[0] + size[0],
            topleft[1] + size[1],
        )
        im = im.crop(topleft + bottomright)

    return im


def choose_pix(directory, max_width, max_height):
    _pix = glob('{}/*.jpg'.format(directory))
    pix = _pix[:]
    for p in _pix:
        size = Image.open(p).size
        if size[0] < max_width or size[1] < max_height:
            pix.remove(p)

    if not pix:
        return

    # we need at least 3 images, so dupe if need be
    while len(pix) < 3:
        pix = pix + pix

    shuffle(pix)

    return  {
        'full': {
            'size': (max_width, max_height),
            'file': pix.pop(),
        },
        'tall': {
            'size': (max_width/2, max_height),
            'file': pix.pop(),
        },
        'wide': {
            'size': (max_width, max_height/2),
            'file': pix.pop(),
        },
    }


if __name__ == '__main__':
    from optparse import OptionParser
    usage = "Usage: %prog [options] picture_dir out_dir"
    parser = OptionParser(usage=usage)
    parser.add_option('-x', '--max-width', type='int', default=SCREEN_WIDTH)
    parser.add_option('-y', '--max-height', type='int', default=SCREEN_HEIGHT)
    parser.add_option('-s', '--sizes', default='full,tall,wide')
    options, args = parser.parse_args()

    if not len(args) == 2:
        parser.error("%prog takes exactly 2 arguments")

    read_dir, out_dir = args
    images = choose_pix(read_dir, options.max_width, options.max_height)

    if not images:
        print 'No suitable images in {}'.format(read_dir)
        exit()

    valid_sizes = images.keys()
    _sizes = options.sizes.split(',')
    sizes = [s.strip() for s in _sizes if s.strip() in valid_sizes] or valid_sizes

    for k in sizes:
        spec = images.get(k)
        new_file = '{}/{}.jpg'.format(out_dir,k)
        try:
            now = datetime.now().strftime('%Y%m%d%H%I%S')
            move(new_file, '{}/{}.{}.jpg'.format(out_dir, k, now))
        except:
            pass
        im = make_bg(spec['file'], spec['size'])
        im.save(new_file)


