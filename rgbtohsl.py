#!/usr/bin/env python


def rgbtohsl(hexcode='ffffff'):
    """
    Adapted from http://goo.gl/EhNlZ
    """
    if hexcode[0] == '#':
        hexcode = hexcode[1:]
    r,g,b = (
        int(hexcode[0:2], 16) / 255.0,
        int(hexcode[2:4], 16) / 255.0,
        int(hexcode[4:6], 16) / 255.0,
    )
    maxval = max([r, g, b])
    minval = min([r, g, b])
    h = s = l = (maxval + minval) / 2.0

    if maxval == minval:
        h = s = 0.0 # achromatic
    else:
        d = maxval - minval
        s = d / (2.0 - (maxval + minval)) if l > 0.5 else d / (maxval + minval)
        h = {
            r: (g - b) / d + (6.0 if g < b else 0.0),
            g: (b - r) / d + 2.0,
            b: (r - g) / d + 4.0,
        }[maxval]
        h = h / 6.0

    return [int(360*h), int(100*s), int(100*l)]

if __name__ == '__main__':
    import sys
    color = sys.argv[1]
    h,s,l = rgbtohsl(color)
    print('{}: {:>3} {:>3} {:>3}'.format(color, h, s, l))
