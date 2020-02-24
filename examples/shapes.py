from devcs import *
from features import *

def num2period(num, feature):
    width = feature.bbox.x2 - feature.bbox.x1
    if num > 1 :
        period = (dbbox.x2 - width)/(num - 1)
    else:
        period = dbbox.x2
    return period

def spacingsreqs(widthfeat,widthspace):
    p = widthfeat + widthspace
    X = dbbox.x2

    n = (X // p) - 1
    x0 = (X - n*p)/2 - widthfeat/2
    if x0 < 0:
        n -= 1
        x0 = (X - n*p)/2 - widthfeat/2

    return p, x0 #- widthfeat/2

feat = Square(5)
squ = Layer(period = num2period(3,feat),
        feature = feat)
feat = Rectangle((10,5))
rec = Layer(period = num2period(4,feat),
        feature = feat)

feat = Semicircle(6)
p, x0 = spacingsreqs(feat.size, 10)
cir = Layer(period = p,
        feature = feat,
        x0 = x0)

feat = EquilateralTriangle(5)
tri = Layer(period = num2period(1,feat),
        feature = feat)

feat = Polygon([(0,0),(5,2),(0,3)])
irr = Layer(period = num2period(6,feat),
        feature = feat)

irc = conformal_layer(irr,0.2)
from pyx import color
irc.color = color.rgb.red

ex = Layer(feature=Rectangle((100,1)))

s = Schematic()
d = Device()
d.stack(squ)
d.stack(rec)
d.stack(cir)
d.stack(tri)
d.stack([irc,irr])
d.stack(ex)

s.stack(d)
s.write('shapes',clip=True)
