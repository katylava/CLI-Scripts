#!/usr/bin/env python

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
            ratio = float(size[0])/im.size[0]
            new_size = (size[0], int(ratio*im.size[1]))
        else:
            ratio = float(size[1])/im.size[1]
            new_size = (int(ratio*im.size[0]), size[1])
        try:
            im = im.resize(new_size, Image.ANTIALIAS)
        except:
            raise GenerateImageError("Failed resize: {}".format(file))

    #crop
    width_diff = im.size[0] - size[0]
    height_diff = im.size[1] - size[1]
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
        except:
            raise GenerateImageError("Failed crop: {}".format(file))

    return im

def choose_pix(directory, max_width, max_height, ratios=None, pattern=None):
    search = pattern or '{}/*.jpg'
    _pix = glob(search.format(directory))
    pix = _pix[:]
    for p in _pix:
        size = Image.open(p).size
        if size[0] < max_width or size[1] < max_height:
            pix.remove(p)

    if not pix:
        return

    if not ratios:
       ratios = DEFAULT_RATIOS

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
    parser.add_option('-x', '--max-width', type='int', default=SCREEN_WIDTH)
    parser.add_option('-y', '--max-height', type='int', default=SCREEN_HEIGHT)
    parser.add_option('-f', '--file-name',
                      help='Name for output file. Uses size if not given.')
    parser.add_option('-b', '--backup', action='store_true',
                      help='Create backup of existing file.')
    parser.add_option('-s', '--sizes', help='Choose full, tall, and/or wide',
                      default='full,tall,wide')
    parser.add_option('-l', '--list', action='store_true',
                      help='List current sizes in out_dir')
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

    if options.list:
        list_sizes(out_dir)
        exit()

    ratios = None
    if options.custom:
        if options.width < 0 or options.width > 1 \
                or options.height < 0 or options.height > 1:
            parser.error("width and height options must be between 0 and 1")
        sizes = [options.name]
        ratios = ((options.name, options.width, options.height),)
    else:
        default_sizes = [t[0] for t in DEFAULT_RATIOS]
        sizes = options.sizes.split(',')
        extra_sizes = [s for s in sizes if s not in default_sizes]
        ratios = [t for t in DEFAULT_RATIOS if t[0] in sizes]
        for s in extra_sizes:
            size = get_size_from_image(s, out_dir)
            if size:
                ratios.append((
                    s,
                    float(size[0])/options.max_width,
                    float(size[1])/options.max_height,
                ))
            else:
                print("Error: can't get size for {}".format(s))

    images = choose_pix(read_dir, options.max_width, options.max_height, ratios)

    if not images:
        print 'No suitable images in {}'.format(read_dir)
        exit()

    num_images = len(sizes)
    for k in sizes:
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
            im = make_bg(spec['file'], spec['size'])
        except GenerateImageError as e:
            print("\tError generating image: {}".format(e.message))
        else:
            try:
                im.save(new_file)
            except Exception as e:
                print("\tError saving image to {}: {}".format(new_file, e.message))
                if backup:
                    move(backup, new_file)


