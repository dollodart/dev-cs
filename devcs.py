from numpy.linalg import norm
from numpy import array, roll, sqrt, argmin
from math import ceil, inf
from pyx import path, canvas, color as pyxcolor, text
text.set(text.UnicodeEngine)
from numpy import arctan2, sqrt

class Bbox():
    """A bounding box. One definition of a bounding box in common use is the tuple (x1,y1,x2,y2) where 
    x1 is the x-coordinate of the lower left corner (the minimum x)
    y1 is the y-coordinate of the lower left corner (the minimum y)
    x2 is the x-coordinate of the upper right corner (the maximum x)
    y2 is the y-coordinate of the upper right corner (the maximum y)
    """

    def __init__(self,x1,y1,x2,y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
    def __getitem__(self,i):
        if i == 0:
            return self.x1
        elif i == 1:
            return self.y1
        elif i == 2:
            return self.x2
        elif i == 3:
            return self.y2
        else:
            raise IndexError("Out of range")

    def __setitem__(self,i,v):
        if i == 0:
            self.x1 = v
        elif i == 1:
            self.y1 = v
        elif i == 2:
            self.x2 = v
        elif i == 3:
            self.y2 = v
    def __str__(self):
       return '{} {} {} {}'.format(self.x1,self.y1,self.x2,self.y2)

dbbox = Bbox(0,0,100,100)

eps = 0.01

class Schematic:
    """A schematic is a stack of devices to be laid out in a schematic.
    
    wrap: number of devices to display horizontally before beginning on a new line.
        
        """

    def __init__(self, wrap=10000  # don't use inf since it is floating point and casts integers to floats
                 ):
        self.devices = []
        self.wrap = wrap
        self.current = 0

    def stack(self, device):
        print('stacking device {}'.format(self.current))
        yshift = (dbbox.y2-dbbox.y1)*1.25
        xshift = (dbbox.x2-dbbox.x1)*1.25

        yshift *= self.current % self.wrap
        xshift *= self.current // self.wrap

        for layer in device:
            layer.bbox[0] += xshift
            layer.bbox[1] -= yshift
            layer.bbox[2] += xshift
            layer.bbox[3] -= yshift
            layer.domain = (layer.domain[0] + xshift, layer.domain[1] + xshift)
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
                rect = (lbbox.x1, lbbox.y1, lbbox.x2-lbbox.x1,lbbox.y2-lbbox.y1)
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
    """A device stacks layers. 
    Stacking adjusts the bounding box and the feature y-positions by a shift of the current stack height.
    If more than one layer is provided in one stack call all of the layers are placed on the same plane."""

    def __init__(self):
        self.layers = []
        self.stack_height = 0

    def stack(self, layers):
        if not isinstance(layers, list):
            layers = [layers]
        h = []
        for layer in layers:
            self.layers.append(layer)
            h.append(layer.height)

            for feature in layer:
                feature.y += self.stack_height
            # set the bbox to be on this plane
            layer.bbox.y1 = self.stack_height 
            layer.bbox.y2 = self.stack_height + layer.height 

        self.stack_height += max(h)

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
    """A layer is a set of features uniformly horizontally distributed.
    
    period: The spatial period of the layer. By default it is infinity.
    height: The height of the layer above its base point. Usually this should be equal to the feature height and this is the default value.
    x0: The starting point of the layer laterally (related to trig phase shift by phi = 2 pi x0/period).
    phase_fraction: A fraction from 0 to 1 to offset the layer laterally (related to trig phase shift by factor of 2 pi).
    feature: The profile of the layer, often rectangular but can be traingular or otherwise. By default the layer is equal parts square trough cand crest.
    domain: The domain of the layer. If infinite, it spans the layer bounding box, and this is default.
    lbbox: The bounding box to clip out features from the layer. By default calculated from the layer height and the domain.
    domain_relative_phase: Define the phase relative to the domain by letting x=0 be at the domain start rather than the origin. The phase fraction and x0 are by default not relative to the domain choice.

    aesthetic kwargs: 

    stroke: whether or not the shape should have a boundary
    stroke_color: if there is a boundary, the color of that boundary
    text: a text to indicate the layer

    """

    def __init__(self,
                 period=inf,
                 height=None,
                 phase_fraction=0,
                 x0=0,
                 domain=inf,
                 lbbox=None,
                 feature=None,
                 domain_relative_phase = False,
                 # aesthetic features
                 color=None,
                 stroke=False,
                 stroke_color=None,
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
            print('Both x0 and specified phase fraction are non-zero\nAssuming they both add to the phase shift')

        if domain == inf:
            self.domain = (dbbox.x1, dbbox.x2)
        if period == inf:
            self.period = dbbox.x2 - dbbox.x1

        phase = phase_fraction * self.period

        if self.feature is None:
            edge_length = self.period / 2.
            self.feature = Square(size=edge_length)

        if height is None:
            self.height = self.feature.bbox.y2 - self.feature.bbox.y1

        n = ceil((dbbox.x2 - dbbox.x1) / period)
        l = []

        x = phase + x0
        if domain_relative_phase:
            x += self.domain[0]

        self.feats = []
        for i in range(n):
            if self.domain[0] - eps < x < self.domain[1] + eps:
                feature = self.feature.copy()
                feature.x = x
                self.feats.append(feature)
            x += self.period
            x %= dbbox.x2

        if lbbox == None:
            self.bbox = Bbox(self.domain[0], 0, self.domain[1], self.height)
        else:
            self.bbox = lbbox

    def __getitem__(self, i):
        return self.feats[i]

    def __len__(self):
        return len(self.feats)

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
    """Create a copy of the layer which is magnified slightly. 
    When placed behind the original layer, this looks like a conformal deposition.
    """

    layer = layer.copy()
    for feature in layer:
        feature.magnify(thickness)
    layer.height += thickness
    layer.bbox.y2 += thickness

    return layer


class Feature:
    """

    x: the x-coordinate of the lower left corner of the feature
    y: the y-coordinate of the lower left corner of the feature
    size: a scalar, list of scalars, or list of coordinates which determines the feature size (and sometimes shape) for subclasses

    """
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
        self.bbox = Bbox(x, y, self.x + self.l, self.y + self.l)

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
        self.bbox = Bbox(x, y, self.x + self.w, self.y + self.h)

    def place(self):
        """Places the feature lower left and returns a path object describing the feature perimeter."""
        return path.rect(self.x, self.y, self.w, self.h)

    def magnify(self, thickness):
        """Magnifies the feature to have a layer thickness greater while keeping the center."""
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
        self.bbox = Bbox(x, y, x + 2 * self.r, y + self.r)
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
        self.bbox = Bbox(x, y, x + self.w, y + self.h)

    def place(self):
        return path.path(path.moveto(self.x, self.y),
                         path.lineto(self.x + self.w, self.y + self.h),
                         path.lineto(self.x + self.w, self.y),
                         path.lineto(self.x, self.y))


class EquilateralTriangle(Feature):
    def __init__(self, size, x=0, y=0):
        super().__init__(size, x, y)
        self.a = self.size
        self.bbox = Bbox(x, y, x + self.a, y + self.a*sqrt(3)/2)

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
        xp, yp = zip(*size)
        cop = (sum(xp) / len(xp), sum(yp) / len(yp))
        for point in size:
            phis.append(arctan2(point[1] - cop[1], point[0] - cop[0]))
        s, s_phis = zip(*sorted(zip(size, phis), key=lambda x: -x[1]))
        self.bbox = Bbox(x, y, x + max(xp), y + max(yp))
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
