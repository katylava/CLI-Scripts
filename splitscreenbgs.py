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


def choose_pix(directory, max_width, max_height, ratios=None):
    _pix = glob('{}/*.jpg'.format(directory))
    pix = _pix[:]
    for p in _pix:
        size = Image.open(p).size
        if size[0] < max_width or size[1] < max_height:
            pix.remove(p)

    if not pix:
        return

    if not ratios:
       ratios = (('full',1,1),('tall',.5,1),('wide',1,.5))

    # dupe if need be
    while len(pix) < len(ratios):
        pix = pix + pix

    shuffle(pix)

    specs = {}
    for key, w, h in ratios:
        specs.update({
            key: {
                'size': (int(max_width*float(w)), int(max_height*float(h))),
                'file': pix.pop(),
            }
        })
    return specs



if __name__ == '__main__':
    from optparse import OptionParser, OptionGroup
    usage = "Usage: %prog [options] picture_dir out_dir"
    parser = OptionParser(usage=usage)
    parser.add_option('-x', '--max-width', type='int', default=SCREEN_WIDTH)
    parser.add_option('-y', '--max-height', type='int', default=SCREEN_HEIGHT)
    parser.add_option('-s', '--sizes', help='Choose full, tall, and/or wide',
                      default='full,tall,wide')
    parser.add_option('-c', '--custom', action='store_true',
                      help='Create a single size with ratios specified in'
                           ' custom size options')
    group = OptionGroup(parser, 'Custom size options')
    group.add_option('--name', help='The out file name, no extension',
                     default='custom')
    group.add_option('--width', help='Float between 0 and 1, determines width'
                                     ' of output image by multiplying by'
                                     ' --max-width', type='float', default=1.0)
    group.add_option('--height', help='Float between 0 and 1, determines height'
                                     ' of output image by multiplying by'
                                     ' --max-height', type='float', default=1.0)
    parser.add_option_group(group)
    options, args = parser.parse_args()

    if not len(args) == 2:
        parser.error("%prog takes exactly 2 arguments")

    read_dir, out_dir = args

    ratios = None
    if options.custom:
        ratios = ((options.name, options.width, options.height),)
    images = choose_pix(read_dir, options.max_width, options.max_height, ratios)

    if not images:
        print 'No suitable images in {}'.format(read_dir)
        exit()

    if not options.custom:
        valid_sizes = images.keys()
        _sizes = options.sizes.split(',')
        sizes = [s.strip() for s in _sizes if s.strip() in valid_sizes] or valid_sizes
    else:
        if options.width < 0 or options.width > 1 \
                or options.height < 0 or options.height > 1:
            parser.error("width and height options must be between 0 and 1")
        sizes = [options.name]


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


