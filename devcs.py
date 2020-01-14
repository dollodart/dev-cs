from numpy.linalg import norm
from numpy import array, roll, sqrt, argmin
from math import ceil, inf
from pyx import path, canvas, color as pyxcolor, text
text.set(text.UnicodeEngine)
from numpy import arctan2, sqrt
bbox = (0, 0, 100, 100)


class Schematic:
    """A schematic is a sequence """

    def __init__(self, wrap=10000  # don't use inf since it is floating point and casts integers to floats
                 ):
        self.devices = []
        self.wrap = wrap
        self.current = 0

    def stack(self, device):
        print('stacking device {}'.format(self.current))
        yshift = bbox[-1]*1.25
        xshift = bbox[-2]*1.25

        yshift *= self.current % self.wrap
        xshift *= self.current // self.wrap

        for layer in device:
            layer.bbox[0] += xshift
            layer.bbox[1] -= yshift
            layer.bbox[2] += xshift
            layer.bbox[3] -= yshift
            layer.domain = (layer.domain[0] + xshift, layer.domain[1] + xshift)
#            layer.height = layer.bbox[3]
            for feature in layer:
                feature.x += xshift
                feature.y -= yshift

        self.devices.append(device)
        self.current += 1

    def write(self, filename='schematic'):
        c = canvas.canvas()
        for counter, d in enumerate(self.devices):
            for l in d:
                lbbox = l.bbox
                rect = (lbbox[0], lbbox[1], lbbox[2] -
                        lbbox[0], lbbox[3]-lbbox[1])
                clippath = path.rect(*rect)
                cl = canvas.canvas()
                cl = canvas.canvas([canvas.clip(clippath)])
                if l.stroke == True:
                    cl.stroke(f.place(), [l.stroke_color])
                for f in l:
                    print(f.x,f.y,lbbox)
                    cl.fill(f.place(), [l.color])
                if l.text != '':
                    xc = (lbbox[0]+lbbox[2])/2
                    yc = (lbbox[1]+lbbox[3])/2
                    t = text.Text(l.text, scale=2)
                    cl.text(xc,yc,t)#,[text.halign.boxcenter])
                c.insert(cl)
        c.writeSVGfile(filename)


class Device:
    """A device stacks layers"""

    def __init__(self):
        self.layers = []
        self.stack_height = 0

    def stack(self, layers):
        if not isinstance(layers, list):
            layers = [layers]
        hm = 0
        for layer in layers:
            self.layers.append(layer)
            h = layer.height
            if h > hm:
                hm = h
            for feature in layer:
                feature.y += self.stack_height
            layer.bbox[1] = self.stack_height
            layer.bbox[3] += self.stack_height
#            layer.height = layer.bbox[3]
        self.stack_height += hm

    def append(self, layer):
        self.layers.append(layer)

    def __getitem__(self, i):
        return self.layers[i]

    def copy(self):
        myd = Device()
        for layer in self.layers:
            myd.append(layer.copy())
        myd.stack_height = self.stack_height
        return myd


class Layer:
    """A layer consists of features uniformly horizontally distributed."""

    def __init__(self,
                 period=inf,
                 height=None,
                 phase_fraction=0,
                 domain=inf,
                 x0=0,
                 feature=None,
                 # aesthetic features
                 color=None,
                 stroke=False,
                 stroke_color=None,
                 lbbox=None,
                 text=''):

        self.period = period
        self.height = height
        self.phase_fraction = phase_fraction
        self.domain = domain
        self.feature = feature
        self.stroke = stroke
        self.text = text

        if color == None:
            self.color = pyxcolor.rgb.black
        else:
            self.color = color
        if stroke_color == None:
            self.stroke_color = pyxcolor.rgb.black
        else:
            self.stroke_color = stroke_color

        # checking user inputs
        if x0 != 0 and phase_fraction != 0:
            print('Both x0 and specified phase fraction are non-zero, assuming they add')

        if domain == inf:
            self.domain = domain = (bbox[0], bbox[2])
        if period == inf:
            self.period = period = bbox[2] - bbox[0]

        phase = phase_fraction * period

        if feature is None:  # assume square, and padding equals feature width
            edge_length = period / 2.
            self.feature = Square(size=edge_length)
        # else use the provided feature

        if height is None:
            self.height = feature.bbox[3]

        n = ceil((bbox[2] - bbox[0]) / period)
        l = []

        x = phase + x0
        y = 0
        self.l = []
        for i in range(n):
            if domain[0] - eps < x < domain[1] + eps:
                feature = self.feature.copy()
                feature.x = x
                self.l.append(feature)
            x += period
            x %= bbox[2]

        if lbbox == None:
            self.bbox = [domain[0], 0, domain[1], self.height]
        else:
            self.bbox = lbbox

    def __getitem__(self, i):
        return self.l[i]

    def __len__(self):
        return len(self.l)

    def copy(self):
        return self.__class__(period=self.period,
                              height=self.height,
                              phase_fraction=self.phase_fraction,
                              domain=self.domain,
                              feature=self.feature,
                              color=self.color,
                              stroke=self.stroke,
                              lbbox=self.bbox)


def conformal_layer(layer, thickness):
    layer = layer.copy()
    for feature in layer:
        feature.magnify(thickness)
    return layer


eps = 0.01
class Feature:
    def __init__(self, size, x, y):
        self.size = size
        self.x = x
        self.y = y

    def copy(self):
        return self.__class__(size=self.size, x=self.x, y=self.y)

class Square(Feature):
    def __init__(self, size, x=0, y=0):
        super().__init__(size, x, y)
        self.l = self.size
        self.bbox = (x, y, self.l, self.l)

    def place(self):
        xll = self.x
        yll = self.y
        w = h = self.l
        return path.rect(xll, yll, w, h)

    def magnify(self, magnification):
        self.x += (1 - magnification) * l / 2
        self.l *= magnification


class Rectangle(Feature):
    def __init__(self, size, x=0, y=0):
        super().__init__(size, x, y)
        self.w = self.size[0]
        self.h = self.size[1]
        self.bbox = (x, y, self.w, self.h)

    def place(self):
        """Places the feature lower left and returns a path object describing the feature perimeter."""
        return path.rect(self.x, self.y, self.w, self.h)

    def magnify(self, thickness):
        """Magnifies the feature to have a layer thickness greater while maintaing its center."""
        mw = 1 + 2 * thickness / self.w
        mh = 1 + 2 * thickness / self.h
        self.x -= (mw - 1) * self.w / 2
        self.y -= (mh - 1) * self.h / 2
        self.w *= mw
        self.h *= mh


class Semicircle(Feature):
    def __init__(self, size, x=0, y=0):
        super().__init__(size, x, y)
        self.r = self.size
        self.bbox = (x, y, 2 * self.r, self.r)
        self.w = 2*self.r

    def place(self):
        return path.path(
            path.arc(
                self.x +
                self.r,
                self.y,
                self.r,
                0,
                180),
            path.lineto(
                self.x +
                2 *
                self.r,
                self.y))

    def magnify(self, thickness):
        magnification = 1 + thickness/self.r
        self.x += (1 - magnification) * self.r
        self.r *= magnification
        self.w = 2*self.r


class RightTriangleUp(Feature):
    def __init__(self, size, x=0, y=0):
        super().__init__(size, x, y)
        self.w = self.size[0]
        self.h = self.size[1]
        self.bbox = (x, y, self.w, self.h)

    def place(self):
        return path.path(path.moveto(self.x, self.y),
                         path.lineto(self.x + self.w, self.y + self.h),
                         path.lineto(self.x + self.w, self.y),
                         path.lineto(self.x, self.y))


class EquilateralTriangle(Feature):
    def __init__(self, size, x=0, y=0):
        super().__init__(size, x, y)
        self.a = self.size
        self.bbox = (x, y, self.a, self.a*sqrt(3)/2)

    def place(self):
        return path.path(path.moveto(self.x, self.y),
                         path.lineto(self.x + self.a/2,
                                     self.y + self.a*sqrt(3)/2),
                         path.lineto(self.x + self.a, self.y),
                         path.closepath())

    def magnify(self, magnification):
        self.x += (1 - magnification) * self.a / 2
        self.a *= magnification


class Polygon(Feature):
    # size is actually point coordinates
    def __init__(self, size, x=0, y=0):
        super().__init__(size, x, y)
        phis = []
        x, y = zip(*size)
        cop = (sum(x) / len(x), sum(y) / len(y))
        for point in size:
            phis.append(arctan2(point[1] - cop[1], point[0] - cop[0]))
        s, s_phis = zip(*sorted(zip(size, phis), key=lambda x: -x[1]))
        self.bbox = (x, y, max(x), max(y))
        self.s = s

    def place(self):
        paths = [path.moveto(self.x, self.y)]
        for point in self.s:
            paths.append(path.lineto(self.x + point[0], self.y + point[1]))
        paths.append(path.closepath())
        return path.path(*paths)

    def magnify(self, thickness):
        delta = thickness
        rs = array(self.size)

        cop = rs.mean(axis=0)
        rs = rs - cop
        ds = rs - roll(rs, 1, axis=0)
        ds = (ds.T / norm(ds, axis=1)).T
        a = ds - roll(ds, -1, axis=0)
        a = (a.T/norm(a, axis=1)).T
        d = (a.T*delta*norm(rs, axis=1)).T
        rsp = rs + d
        self.s = rsp + cop
        # change the origin of the shape
#        i = argmin(norm(rsp+cop,axis=1))
#        self.x += (rsp + cop)[i][0]
#        self.y += (rsp + cop)[i][1]


if __name__ == '__main__':
    l1 = Layer(10)
    l2 = Layer(10, phase_fraction=0.2)
    l3 = Layer(10, phase_fraction=0.75, feature=Rectangle((2, 2)))
    d = Device()
    l4 = conformal_layer(l3, thickness=0.1)
    base_layer = Layer(100, feature=Rectangle((100, 0.1)))
    l5 = Layer(100, feature=Rectangle((100, 0.1), 0, 0.1))
    l6 = Layer(5, domain=(20, 40), feature=Semicircle(2))
    l7 = Layer(5, domain=(40, 60), feature=RightTriangleUp((1, 2)))
    l8 = Layer(5, domain=(60, 80), feature=Polygon(((0, 0), (2, 3), (3, 1))))
    l9 = Layer(5, phase_fraction=0.5, domain=(
        60, 80), feature=EquilateralTriangle(1))
    l10 = conformal_layer(l6, thickness=0.1)
    l11 = conformal_layer(l10, thickness=0.2)
    l12 = conformal_layer(l8, thickness=0.1)

    [print(f.place()) for f in l8]
    [print(f.place()) for f in l12]

    d.stack(l1)
    d.stack([l2, l4, l5, l3, base_layer])
    d.stack([l11, l10, l6, l7])
    d.stack([l12, l8, l9])

    c = canvas.canvas()
    k = pyxcolor.rgb.black
    r = pyxcolor.rgb.red
    b = pyxcolor.rgb.blue

    colors = [k, k, r, r, k, k, b, r, k, k, r, k, k]
    for counter, l in enumerate(d):
        bbox = path.rect(*l.bbox)
        cl = canvas.canvas([canvas.clip(bbox)])
        for f in l:
            cl.fill(f.place(), [colors[counter]])
        c.insert(cl)
    c.writeSVGfile('c-s.svg')
