from devcs import *
from features import *

def num2period(num, fwidth, dwidth):
    if num == 1 :
        period = dwidth
    else:
        period = (dwidth - fwidth)/(num - 1)
    return period

def spacingsreqs(fwidth, swidth, dwidth):
    p = fwidth + swidth
    X = dwidth

    n = (X // p) - 1
    x0 = (X - n*p)/2 - fwidth/2
    if x0 < 0:
        n -= 1
        x0 = (X - n*p)/2 - fwidth/2

    return p, x0

s = Schematic()

for dwidth in 147,:
    feat = Square(5)
    fwidth = feat.get_bbox(0,0)[2] - feat.get_bbox(0,0)[0]
    squ = Layer(period = num2period(3,fwidth,dwidth),
            feature = feat)
    feat = Rectangle(10,5)
    fwidth = feat.get_bbox(0,0)[2] - feat.get_bbox(0,0)[0]
    rec = Layer(period = num2period(4,fwidth,dwidth),
            feature = feat)

    feat = RightTriangleUpBack(6,3)
    fwidth = feat.get_bbox(0,0)[2] - feat.get_bbox(0,0)[0]
    p, x0 = spacingsreqs(fwidth, 10, dwidth)
    rtub = Layer(period = p,
            feature = feat,
            x0 = x0)

    feat = EquilateralTriangle(5)
    fwidth = feat.get_bbox(0,0)[2] - feat.get_bbox(0,0)[0]
    tri = Layer(period = num2period(1,fwidth,dwidth),
            feature = feat)

    feat = ConvexPolygon(
            ((0,0),(5,2),(0,3))
            )
    fwidth = feat.get_bbox(0,0)[2] - feat.get_bbox(0,0)[0]
    irr = Layer(period = num2period(6,fwidth,dwidth),
            feature = feat)

    ex = Layer(feature=Rectangle(100,1))

    d = Device(width=dwidth)
    d.stack(squ)
    d.stack(rec)
    d.stack(rtub)
    d.stack(tri)
    d.stack(irr)
    d.stack(ex)

    s.stack(d.copy())
    s.write_ref(100,0,100,d.stack_height)

s.write(f'shapes')
