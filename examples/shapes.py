from devcs import *
from features import *
from time import time
from convfuncs import num2period, spacingsreqs

s = Schematic()

t0 = time()
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

    feat = EquilateralTriangle(5)
    fwidth = feat.get_width()
    p, x0 = spacingsreqs(fwidth, 10, dwidth)
    trap = Layer(period = p,
            feature = feat,
            x0 = x0,
            height = 3)


    d = Device(width=dwidth)
    d.stack(squ)
    d.stack(rec)
    d.stack(rtub)
    d.stack(tri)
    d.stack(irr)
    d.stack(ex)
    d.stack(trap)

    s.stack(d.copy())
    s.stroke_line(100,0,100,d.stack_height)

s.write(f'shapes')
print(time() - t0)
