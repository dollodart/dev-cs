from math import floor


def num2period(num, fwidth, dwidth):
    if num == 1:
        period = dwidth
    else:
        period = (dwidth - fwidth) / (num - 1)
    return period


def num2period_half(num, fwidth, dwidth):
    return dwidth / num, -fwidth / 2


def spacingsreqs(fwidth, swidth, dwidth):
    p = fwidth + swidth
    d = dwidth - fwidth
    n = floor(d / p)
    return p, 0.5 * (d - n * p)
