#!/usr/bin/env python

import fnmatch
from datetime import datetime
from shutil import move
from random import shuffle, randrange
from glob import glob
from PIL import Image

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800
DEFAULT_RATIOS = (('full',1,1),('tall',.5,1),('wide',1,.5))

class GenerateImageError(Exception):
    pass

def make_bg(file, size, resize_threshhold=3000):
    im = Image.open(file)
    orient = 'wide' if size[0] > size[1] else 'tall'

    if 0 in im.size:
        raise GenerateImageError("Can't read size of {}".format(file))

    # fit to width (or height if target is tall) before cropping
    if im.size[0] >= resize_threshhold or im.size[1] >= resize_threshhold:
        if orient == 'wide':
            ratio = float(size[1])/im.size[1]
        else:
            ratio = float(size[0])/im.size[0]
        new_size = (int(ratio*im.size[0]), int(ratio*im.size[1]))
        try:
            im = im.resize(new_size, Image.ANTIALIAS)
        except Exception as e:
            raise GenerateImageError(
                    "Failed resize: {}\nError: {}".format(file, e.message))

    #crop
    width_diff = abs(im.size[0] - size[0])
    height_diff = abs(im.size[1] - size[1])
    if width_diff or height_diff:
        x_crop = 0 if not width_diff else randrange(0, width_diff)
        y_crop = 0 if not height_diff else randrange(0, height_diff)
        topleft = (x_crop, y_crop)
        bottomright = (
            topleft[0] + size[0],
            topleft[1] + size[1],
        )
        try:
            im = im.crop(topleft + bottomright)
        except Exception as e:
            raise GenerateImageError(
                    "Failed crop: {}\nError: {}".format(file, e.message))

    return im

def choose_pic(directory, min_width, min_height, pattern=None):
    search = pattern or '{}/*.jpg'
    if hasattr(directory, '__iter__'):
        _pix = fnmatch.filter(directory, search)
    else:
        _pix = glob(search.format(directory))

    pix = _pix[:]
    shuffle(pix)

    for p in pix:
        size = Image.open(p).size
        if size[0] >= min_width and size[1] >= min_height:
            return p

def get_specs(directory, tot_width, tot_height, ratios=None, pattern=None):
    search = pattern or '{}/*.jpg'
    pix = glob(search.format(directory))

    if not ratios:
       ratios = DEFAULT_RATIOS

    specs = {}
    for prefix, w_ratio, h_ratio in ratios:
        width = int(tot_width*float(w_ratio))
        height = int(tot_height*float(h_ratio))
        specs.update({
            prefix: {
                'size': (width, height),
                'file': choose_pic(pix, width, height, pattern),
            }
        })

    return specs

def get_size_from_image(name, directory, pattern='{}/{}.jpg'):
    search = pattern.format(directory, name)
    matches = glob(search)
    if matches:
        sample = matches[0]
        size = Image.open(sample).size
        return size if 0 not in size else None
    else:
        print('No images matching {}'.format(search))
        return None

def list_sizes(out_dir):
        p = glob('{}/*.jpg'.format(out_dir))
        get_basename = lambda x: x.split('/')[-1].split('.')[0]
        names = [get_basename(pic) for pic in p]
        sizes = sorted(set(names))
        for s in sizes:
            primary = '{}/{}.jpg'.format(out_dir, s)
            if primary in p:
                im  = Image.open(primary)
                w, h = im.size
                ratio = float(w)/float(h)
            else:
                w = h = ''
                ratio = 0
            print('{:>4}x{:<4} {:1.2f} {}'.format(w, h, ratio, s))

if __name__ == '__main__':
    from subprocess import Popen, PIPE
    from optparse import OptionParser, OptionGroup
    usage = "Usage: %prog [options] picture_dir out_dir"
    parser = OptionParser(usage=usage)
    parser.add_option('-x', '--tot-width', type='int', default=SCREEN_WIDTH)
    parser.add_option('-y', '--tot-height', type='int', default=SCREEN_HEIGHT)
    parser.add_option('-f', '--file-name',
                      help='Name for output file. Uses prefix if not given.')
    parser.add_option('-t', '--threshhold', type='int',
                      help="Width or height beyond which image should be resized"
                           " instead of cropped")
    parser.add_option('-b', '--backup', action='store_true',
                      help='Create backup of existing file.')
    parser.add_option('-p', '--prefixes', help='Choose full, tall, and/or wide',
                      default='full,tall,wide')
    parser.add_option('-l', '--list', action='store_true',
                      help='List current sizes in out_dir')
    parser.add_option('-c', '--custom', action='store_true',
                      help='Create a single size with ratios specified in'
                           ' custom size options')
    group = OptionGroup(parser, 'Custom size options')
    group.add_option('--prefix', help='The out file name, no extension',
                     default='custom')
    group.add_option('--width', help='Float between 0 and 1, determines width'
                                     ' of output image by multiplying by'
                                     ' --tot-width', type='float', default=1.0)
    group.add_option('--height', help='Float between 0 and 1, determines height'
                                     ' of output image by multiplying by'
                                     ' --tot-height', type='float', default=1.0)
    parser.add_option_group(group)
    options, args = parser.parse_args()

    if not len(args) == 2:
        parser.error("%prog takes exactly 2 arguments")

    read_dir, out_dir = args

    if options.list:
        list_sizes(out_dir)
        exit()

    ratios = None
    if options.custom:
        if options.width < 0 or options.width > 1 \
                or options.height < 0 or options.height > 1:
            parser.error("width and height options must be between 0 and 1")
        prefixes = [options.prefix]
        ratios = ((options.prefix, options.width, options.height),)
    else:
        default_prefixes = [t[0] for t in DEFAULT_RATIOS]
        prefixes = options.prefixes.split(',')
        extra_sizes = [s for s in prefixes if s not in default_prefixes]
        ratios = [t for t in DEFAULT_RATIOS if t[0] in prefixes]
        for s in extra_sizes:
            size = get_size_from_image(s, out_dir)
            if size:
                ratios.append((
                    s,
                    float(size[0])/options.tot_width,
                    float(size[1])/options.tot_height,
                ))
            else:
                print("Error: can't get size for {}".format(s))

    images = get_specs(read_dir, options.tot_width, options.tot_height, ratios)

    if not images:
        print 'No suitable images in {}'.format(read_dir)
        exit()

    num_images = len(prefixes)
    for k in prefixes:
        im = None # otherwise if error prev size is saved as current size

        if options.file_name and num_images > 1:
            basename = '{}-{}'.format(k, options.file_name)
        else:
            basename = options.file_name or '{}.jpg'.format(k)
        print("Generating {}".format(basename))

        spec = images.get(k)
        new_file = '{}/{}'.format(out_dir,basename)
        now = datetime.now().strftime('%Y%m%d%H%I%S')

        if options.backup:
            backup = '{}/{}.{}.{}'.format(out_dir, k, now, basename)
            try:
                move(new_file, backup)
            except:
                print("\tError creating backup file {}".format(backup))
                backup = None

        try:
            im = make_bg(spec['file'], spec['size'],
                         resize_threshhold=options.threshhold)
        except GenerateImageError as e:
            print("\tError generating image: {}".format(e.message))
        else:
            try:
                im.save(new_file)
            except Exception as e:
                print("\tError saving image to {}: {}".format(new_file, e.message))
                if backup:
                    move(backup, new_file)


