from numpy.linalg import norm
from numpy import array, roll, sqrt, argmin
from math import ceil, floor, nan, isnan
from pyx import path, canvas as pyxcanvas, color as pyxcolor, text, style
text.set(text.UnicodeEngine)
from numpy import arctan2, sqrt
from features import *
from collections import deque

eps = 0.01 # numerical tolerance

class Schematic:
    """Schematic lays out the stack of devices.
    
    wrap: 
        type: int
        default: 10000
        description: number of devices to display vertically before beginning on a new column.
    ysep:
        type: float
        default: 100.
        description: y-separation of devices in schematic
    xsep: 
        type: float
        default: 50.
        description: x-separation of devices in schematic
    devices_xy:
        type: deque
        default: empty deque
        description: deque of 2-tuples, index 0 is Device object, index 1 is 2-tuple of x- and y-shift
    current_position:
        type: int
        default: 0
        description: current position is the current number of devices which determines modulo wrap the x- and y-shift
    canvas:
        type: pyxcanvas.canvas
        default: None
        description: the canvas on which to draw the schematic

    """

    def __init__(self, wrap=10000  # don't use inf/nan since it is floating point and casts integers to floats
                 , ysep = 100.
                 , xsep = 50.
                 , devices_xy = deque()
                 , current_position = 0
                 , canvas = None):
        self.wrap = wrap
        self.current_position = current_position
        self.devices_xy = devices_xy
        self.xsep = xsep
        self.ysep = ysep
        if canvas is None:
            self.canvas = pyxcanvas.canvas()

    def __len__(self):
        return len(self.devices)

    def stack(self, device):
        yshift = -1*self.ysep
        xshift = self.xsep
        yshift *= self.current_position % self.wrap
        xshift *= self.current_position // self.wrap

        self.devices_xy.append((device,(xshift,yshift)))
        self.current_position += 1

    def pop(self, count):
        dp = queue()
        self.current_position -= count
        for i in count:
            dp.append(self.devices_xy.pop())
        return dp

    def place(self, x, y):
        return (d[0].place(x + d[1][0], y + d[1][1]) for d in self.devices_xy)

    def copy(self):
        devices_xy = deque( (d[0].copy(),d[1]) for d in self.devices_xy)
        return self.__class__(devices_xy=devices_xy
                , xsepmult = self.xsepmult
                , ysepmult = self.ysepmult
                , current_position = self.current_position
                , devices_shift = self.devices_shift)

    def reverse(self):
        self.devices_xy.reverse()

    def write(self, filename='schematic'):
        schpath = self.place(0, 0)
        for cdev, devpath in enumerate(schpath):
            for clay, laypath in enumerate(devpath):
                laypath, laybbox, laytext = laypath
                laybbox_path = laybbox.to_path()
                laycanv = pyxcanvas.canvas([
                    pyxcanvas.clip(laybbox_path)])

                for cfea, feapath in enumerate(laypath):
                    feapath, color, stroke_color = feapath
                    laycanv.fill(feapath, [color])
                    if stroke_color is None:
                        laycanv.stroke(feapath, [stroke_color])

                if laytext != '':
                    xc = (laybbox.x1+laybbox.x2)/2
                    yc = (laybbox.y1+laybbox.y2)/2
                    t = text.Text(laytext, scale=2)
                    laycanv.text(xc,yc,t)

                self.canvas.insert(laycanv)

        self.canvas.writeEPSfile(filename)

    def stroke_line(self, x1, y1, x2, y2):
        self.canvas.stroke(path.line(x1,y1,x2,y2), [style.linewidth.THICK, pyxcolor.rgb.red])

class Device:
    """A device stacks layers. 
    Stacking adjusts the bounding box and the feature y-positions by a shift of the current stack height.
    If more than one layer is provided in one stack call all of the layers are placed on the same plane.

    layers_y:
        type: deque
        default: empty deque
        description: deque of 2-tuples, Layer objects at index 0 and y position at index 1
    stack_height: 
        type: float
        default: 0.
        description: the current height of the stack onto which further layers should be stacked
    width: 
        type: float
        default: 100.
        description: the width of the device which determines how layers stacked in the device will be clipped
    
    """

    def __init__(self,layers_y = deque(),stack_height=0.,width=100.): 
        self.layers_y = layers_y
        self.stack_height = stack_height
        self.width = width

    def stack(self, layers):
        if not isinstance(layers, list) and not isinstance(layers, tuple):
            layers = (layers,)

        self.layers_y.extend((l,self.stack_height) for l in layers)
        self.stack_height += max(layer.height for layer in layers)

    def pop(self, count): #count is number of layers
        p = deque()
        for i in range(count - 1):
            p.append(self.layers_y.pop())
        pt = self.layers_y.pop()
        self.stack_height = pt[1]
        p.append(pt)
        return p

    def place(self, x, y):
        return (l[0].place(x,y+l[1],self.width) for l in self.layers_y)

    def reverse(self):
        self.layers_y.reverse()

    def copy(self):
        layers_y = deque( (l[0].copy(),l[1]) for l in self.layers_y)
        return Device(layers_y=layers_y,
                stack_height=self.stack_height,
                width=self.width)

class Layer:
    """A layer is a set of features uniformly distributed in the x-direction and with a finite y-dimension.
    
    period: 
        type: float
        default: nan
        description: The x-direction period of the feature in the layer. 
    height:
        type: float
        default: feature height
        description: The y-direction dimension of the layer (used for clipping).
    x0:
        type: float
        default: 0.
        description: The starting point of the layer in the x-direction relative to the device (phase shift = 2 pi x0/period).
    phase_fraction:
        type: float
        default: 0.
        description: A fraction from 0 to 1 to offset the layer in the x-direction (phase shift = 2 pi phase_fraction)
    feature: 
        type: Feature
        default: Equal parts square trough and crest
        description: The profile of the layer, what is repeated. 
    text:
        type: str
        default: ''
        description: text to be describe the layer (placed in the center of the layer bounding box)

    """

    def __init__(self,
                 period=nan,
                 height=None,
                 phase_fraction=0,
                 x0=0,
                 feature=None,
                 color=None,
                 text=''):

        self.period = period
        self.height = height
        self.phase_fraction = phase_fraction
        self.x0 = x0
        self.feature = feature
        self.text = text

        # default handling

        if self.x0 != 0 and self.phase_fraction != 0:
            print('Both x0 and specified phase fraction are non-zero\nAssuming they both add to the phase shift')

        if self.feature is None:
            self.feature = Square(a=self.period / 2.)

        if self.height is None:
            self.height = self.feature.get_height()
        self.x = x0

        if not isnan(self.period):
            self.x += self.phase_fraction * self.period

    def place(self, x, y, width):

        bbox = Bbox(x, y, x+width, y+self.height)
        x = self.x + x
        # if not domain relative phase shift (unlikely) 
        # x = self.x + (bbox.x1 // self.period)*self.period
        # if self.x < bbox.x1 % self.period:
        #     x += self.period
        if isnan(self.period):
            feats = ( (self.feature.place(x, y),), bbox, self.text)
            return feats
        fwidth = self.feature.get_width()
        # condition: i < ((1+eps)*width - fwidth - x)/self.period    
        n = ((1+eps)*width - self.x - fwidth) / self.period 
        n = ceil(n) + 1 # plus 1 for clipping
        feats = tuple(self.feature.place(x + i*self.period,y) for i in range(n))
        return (feats, bbox, self.text)

    def copy(self):
        return self.__class__(
                 period=self.period,
                 height=self.height,
                 phase_fraction=self.phase_fraction,
                 x0=self.x0,
                 feature=self.feature, # features don't need to be copied
                 text=self.text)
