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

def get_size_from_image(name, directory):
    matches = glob('{}/{}*.jpg'.format(directory, name))
    if matches:
        sample = matches[0]
        size = Image.open(sample).size
        return size if 0 not in size else None
    else:
        return None



if __name__ == '__main__':
    from subprocess import Popen, PIPE
    from optparse import OptionParser, OptionGroup
    usage = "Usage: %prog [options] picture_dir out_dir"
    parser = OptionParser(usage=usage)
    parser.add_option('-x', '--max-width', type='int', default=SCREEN_WIDTH)
    parser.add_option('-y', '--max-height', type='int', default=SCREEN_HEIGHT)
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
        p = Popen("cd {} && ls *.jpg".format(out_dir),
                  shell=True, stdin=PIPE, stdout=PIPE).communicate()
        names = [pic.split('.')[0] for pic in p[0].split('\n')]
        _sizes = sorted(set(names))
        sizes = _sizes if _sizes[0] else _sizes[1:]
        for s in sizes:
            print(s)
        print("\nGenerate new image for each size with option:\n"
              "-s {}".format(','.join(sizes)))
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

    for k in sizes:
        im = None # otherwise if error prev size is saved as current size

        print("Generating {}.jpg".format(k))

        spec = images.get(k)
        new_file = '{}/{}.jpg'.format(out_dir,k)
        now = datetime.now().strftime('%Y%m%d%H%I%S')
        backup = '{}/{}.{}.jpg'.format(out_dir, k, now)

        try:
            move(new_file, backup)
        except:
            backup = None

        try:
            im = make_bg(spec['file'], spec['size'])
        except GenerateImageError as e:
            print("\tError generating image: {}".format(e.message))
        else:
            try:
                im.save(new_file)
            except Exception as e:
                print("\tError saving image: {}".format(e.message))


