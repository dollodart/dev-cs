from numpy.linalg import norm
from numpy import array, roll, sqrt, argmin
from math import ceil, inf
from pyx import path, canvas, color as pyxcolor, text
text.set(text.UnicodeEngine)
from numpy import arctan2, sqrt
from features import *

dbbox = Bbox(0,0,100,100) # dbbox must have x1,y1 = 0
eps = 0.01

class Schematic:
    """A schematic is a stack of devices to be laid out in a schematic.
    
    wrap: number of devices to display horizontally before beginning on a new line.
        
        """

    def __init__(self, wrap=10000  # don't use inf since it is floating point and casts integers to floats
                 ):
        self.devices = []
        self.wrap = wrap
        self.current_position = 0
        self.devices_shift = []

    def __len__(self):
        return len(self.devices)

    def stack(self, device):
        yshift = -1*(dbbox.y2-dbbox.y1)*1.25
        xshift = (dbbox.x2-dbbox.x1)*1.25
        yshift *= self.current_position % self.wrap
        xshift *= self.current_position // self.wrap

        self.devices_shift.append([xshift,yshift])
        self.devices.append(device)
        self.current_position += 1

    def write(self, filename='schematic', clip = True):

        c = canvas.canvas()
        for counter, dev in enumerate(self.devices):
            xd = self.devices_shift[counter][0]
            yd = self.devices_shift[counter][1]
            for counter2, lay in enumerate(dev):
                xl = 0
                yl = dev.stack_heights[counter2]

                lbbox = lay.bbox
                rect = (lbbox.x1 + xd + xl, lbbox.y1 + yd + yl, 
                        lbbox.x2-lbbox.x1,lbbox.y2-lbbox.y1)
                clippath = path.rect(*rect)

                if clip:
                    clay = canvas.canvas([canvas.clip(clippath)])
                else:
                    clay = canvas.canvas()

                for counter3,feat in enumerate(lay):
                    xf = feat
                    yf = 0

                    xt = xd + xl + xf
                    yt = yd + yl + yf

                    clay.fill(lay.feature.place(xt, yt), [lay.color])
                    if lay.stroke == True:
                        clay.stroke(feat.place(xt, yt), [lay.stroke_color])

                if lay.text != '':
                    xc = (lbbox[0]+lbbox[2])/2
                    yc = (lbbox[1]+lbbox[3])/2
                    t = text.Text(lay.text, scale=2)
                    clay.text(xc,yc,t)#,[text.halign.boxcenter])

                c.insert(clay)
        c.writeEPSfile(filename)


class Device:
    """A device stacks layers. 
    Stacking adjusts the bounding box and the feature y-positions by a shift of the current stack height.
    If more than one layer is provided in one stack call all of the layers are placed on the same plane.

    stack_heights: the height of each layer in the device stack
    
    """

    def __init__(self,layers = [],stack_heights = [0]):
        self.layers = layers
        self.stack_heights = stack_heights

    def stack(self, layers):
        if not isinstance(layers, list):
            layers = [layers]

        h = []
        for layer in layers:
            self.layers.append(layer)
            h.append(layer.height)

        if len(self.stack_heights) == 0:
            x = 0
        else:
            x = self.stack_heights[-1]

        self.stack_heights += [self.stack_heights[-1]]*(len(layers)-1) \
        + [max(h) + self.stack_heights[-1]]

    def __getitem__(self, i):
        return self.layers[i]

    def copy(self):
        layers = [layer.copy() for layer in self.layers]
        return Device(layers=layers,
                stack_heights=self.stack_heights)


class Layer:
    """A layer is a set of features uniformly horizontally distributed.
    
    period: The spatial period of the layer. By default it is infinity.
    height: The height of the layer above its base point. Usually this should be equal to the feature height and this is the default value.
    x0: The starting point of the layer laterally (related to trig phase shift by phi = 2 pi x0/period).
    phase_fraction: A fraction from 0 to 1 to offset the layer laterally (related to trig phase shift by factor of 2 pi).
    feature: The profile of the layer, often rectangular but can be traingular or otherwise. By default the layer is equal parts square trough cand crest.
    domain: The domain of the layer. If infinite, it spans the layer bounding box, and this is default.
    bbox: The bounding box to clip out features from the layer. By default calculated from the layer height and the domain.
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
                 bbox=None,
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
        self.x0 = x0
        self.domain = domain
        self.bbox = bbox
        self.feature = feature
        self.domain_relative_phase = domain_relative_phase
        self.color = color
        self.stroke = stroke
        self.stroke_color = stroke_color
        self.text = text

        # default handling

        if self.color == None:
            self.color = pyxcolor.rgb.black

        if stroke_color == None:
            self.stroke_color = pyxcolor.rgb.black

        if self.x0 != 0 and self.phase_fraction != 0:
            print('Both x0 and specified phase fraction are non-zero\nAssuming they both add to the phase shift')

        if self.domain == inf:
            self.domain = (dbbox.x1, dbbox.x2)

        if self.period == inf:
            self.period = dbbox.x2 - dbbox.x1

        if self.feature is None:
            self.feature = Square(size=self.period / 2.)

        if self.height is None:
            self.height = self.feature.bbox.y2 - self.feature.bbox.y1

        if bbox == None:
            self.bbox = Bbox(self.domain[0], 0, self.domain[1], self.height)

        x = x0 + self.phase_fraction * self.period

        if self.domain_relative_phase:
            x += self.domain[0]

        # feature creating

        n = ceil((dbbox.x2 - dbbox.x1) / self.period)
        l = []
        self.feats = []

        for i in range(n):
            if self.domain[0] - eps < x < self.domain[1] + eps:
                self.feats.append(x)
            x += self.period
            if x // dbbox.x2 > 1:
                break

    def __getitem__(self, i):
        return self.feats[i]

    def __len__(self):
        return len(self.feats)

    def copy(self):
        return self.__class__(
                 period=self.period,
                 height=self.height,
                 phase_fraction=self.phase_fraction,
                 x0=self.x0,
                 domain=self.domain,
                 bbox=self.bbox,
                 feature=self.feature.copy(), # oop
                 domain_relative_phase = self.domain_relative_phase,
                 color=self.color,
                 stroke=self.stroke,
                 stroke_color=self.stroke_color,
                 text=self.text)

def conformal_layer(layer, thickness):
    """Create a copy of the layer which is magnified slightly. 
    When placed behind the original layer, this looks like a conformal deposition.
    """

    layer = layer.copy()
    layer.feature.magnify(thickness)
    layer.height += thickness
    layer.bbox.y2 += thickness

    return layer
