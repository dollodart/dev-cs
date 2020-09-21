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
    """A schematic is a stack of devices to be laid out in a schematic.
    
    wrap: number of devices to display vertically before beginning on a new column.

    """

    def __init__(self, wrap=10000  # don't use inf/nan since it is floating point and casts integers to floats
                 , ysepmult = 2
                 , xsepmult = 1.25
                 , devices_xy = deque()
                 , current_position = 0
                 , canvas = None):
        self.wrap = wrap
        self.current_position = current_position
        self.devices_xy = devices_xy
        self.xsepmult = xsepmult
        self.ysepmult = ysepmult
        if canvas is None:
            self.canvas = pyxcanvas.canvas()

    def __len__(self):
        return len(self.devices)

    def stack(self, device):
        yshift = -1*device.stack_height*self.ysepmult
        xshift = device.width*self.xsepmult
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
                #laycanv = pyxcanvas.canvas()
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

    def write_ref(self, x1, y1, x2, y2):
        self.canvas.stroke(path.line(x1,y1,x2,y2), [style.linewidth.THICK, pyxcolor.rgb.red])

class Device:
    """A device stacks layers. 
    Stacking adjusts the bounding box and the feature y-positions by a shift of the current stack height.
    If more than one layer is provided in one stack call all of the layers are placed on the same plane.

    layers: the list of layers in the defices
    stack_height: the current height of the stack
    stack_base: the list of heights at which each layer is based 
    width: the width of the device
    
    """

    def __init__(self,layers_y = deque(),stack_height=0,width=100): 
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
                 period=nan,
                 height=None,
                 phase_fraction=0,
                 x0=0,
                 feature=None,
                 domain_relative_phase = False,
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
        # condition = (x + i*self.period + fwidth) / width < 1 + eps:
        # equivalently, i < ((1+eps)*width - fwidth - x)/self.period    
        n = ((1+eps)*width - x - fwidth) / self.period 
        n = ceil(n) + 1 # plus 1 for clipping
        #print(self.feature, n, width, (x + n*self.period + fwidth)/width)
        feats = tuple(self.feature.place(x + i*self.period,y) for i in range(n))
        return (feats, bbox, self.text)

    def copy(self):
        return self.__class__(
                 period=self.period,
                 height=self.height,
                 phase_fraction=self.phase_fraction,
                 x0=self.x0,
                 feature=self.feature, # features don't need to be deep copied
                 text=self.text)
