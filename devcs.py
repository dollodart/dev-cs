from numpy.linalg import norm
from numpy import array, roll, sqrt, argmin
from math import ceil, nan, isnan
from pyx import path, canvas, color as pyxcolor, text
text.set(text.UnicodeEngine)
from numpy import arctan2, sqrt
from features import *

eps = 0.01 # numerical tolerance

class Schematic:
    """A schematic is a stack of devices to be laid out in a schematic.
    
    wrap: number of devices to display vertically before beginning on a new column.

    """

    def __init__(self, wrap=10000  # don't use inf/nan since it is floating point and casts integers to floats
                 , ysepmult = 2
                 , xsepmult = 1.25
                 , devices = []
                 , current_position = 0
                 , devices_shift = []):
        self.devices = devices
        self.wrap = wrap
        self.current_position = current_position
        self.devices_shift = devices_shift
        self.xsepmult = xsepmult
        self.ysepmult = ysepmult

    def __len__(self):
        return len(self.devices)

    def stack(self, device):
        yshift = -1*device.stack_height*self.ysepmult
        xshift = device.width*self.xsepmult
        yshift *= self.current_position % self.wrap
        xshift *= self.current_position // self.wrap

        self.devices_shift.append([xshift,yshift])
        self.devices.append(device)
        self.current_position += 1

    def unstack(self, count):
        self.devices_shift = self.devices_shift[:-count]
        self.devices = self.devices[:-count]
        self.current_position -= count

    def reverse(self):
        self.devices = self.devices[::-1]
        #self.devices_shift = self.devices_shift[::-1]

    def place(self, x, y):
        l = []
        for c, dev in enumerate(self.devices):
            x2, y2 = self.devices_shift[c]
            l.append(dev.place(x + x2, y + y2))
        return l

    def copy(self):
        devices = [d.copy() for d in self.devices]
        return self.__clase__(devices=devices
                , xsepmult = self.xsepmult
                , ysepmult = self.ysepmult
                , current_position = self.current_position
                , devices_shift = self.devices_shift)

    def write(self, filename='schematic'):
        c = canvas.canvas()
        devl = self.place(0, 0)
        for cdev, dev in enumerate(devl):
            for clay, lay in enumerate(dev):
                for cfea, fea in enumerate(lay):
                    feat = self.devices[cdev][clay].feature
                    c.fill(fea, [feat.color])
                    c.stroke(fea, [feat.stroke_color])
                    #TODO support clipping

#                if lay.text != '':
#                    xc = (lbbox[0]+lbbox[2])/2
#                    yc = (lbbox[1]+lbbox[3])/2
#                    t = text.Text(lay.text, scale=2)
#                    clay.text(xc,yc,t)#,[text.halign.boxcenter])

        c.writeEPSfile(filename)


class Device:
    """A device stacks layers. 
    Stacking adjusts the bounding box and the feature y-positions by a shift of the current stack height.
    If more than one layer is provided in one stack call all of the layers are placed on the same plane.

    layers: the list of layers in the defices
    stack_height: the current height of the stack
    stack_base: the list of heights at which each layer is based 
    width: the width of the device
    
    """

    def __init__(self,layers = [],stack_base = [],stack_height=0,width=100): 
        self.layers = layers
        self.stack_base = stack_base
        self.stack_height = stack_height
        self.width = width

    def stack(self, layers):
        if not isinstance(layers, list):
            layers = [layers]

        self.stack_base.extend([self.stack_height]*len(layers))

        for layer in layers:
            self.layers.append(layer)

        self.stack_height += max(layer.height for layer in layers)

    def pop(self, count): #count is number of layers
        p = self.layers[-count:]
        self.layers = self.layers[:-count]
        self.stack_height = self.stack_base[-count]
        self.stack_base = self.stack_base[:-count]
        return p

    def place(self, x, y):
        l = []
        for c,layer in enumerate(self.layers):
            l.append(layer.place(x,y+self.stack_base[c],self.width))
        return l

    def __getitem__(self, i):
        return self.layers[i]

    def copy(self):
        layers = [layer.copy() for layer in self.layers]
        return Device(layers=layers,
                stack_height=self.stack_height,
                stack_base=self.stack_base)


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
            self.height = self.feature.get_bbox(0,0).y2 - self.feature.get_bbox(0,0).y1
        self.x = x0

        if not isnan(self.period):
            self.x += self.phase_fraction * self.period

    def place(self, x, y, width):

        feats = []
        xf = self.x + x
        # if not domain relative phase shift (unlikely) 
        # x = self.x + (bbox.x1 // self.period)*self.period
        # if self.x < bbox.x1 % self.period:
        #     x += self.period
        if isnan(self.period):
            feats.append(self.feature.place(xf, y))
            return feats

        while True:
            if (xf - x - self.x) // width > eps:
                break
            feats.append(
                    self.feature.place(xf, y)
                        )
            xf += self.period
        return feats

    def copy(self):
        return self.__class__(
                 period=self.period,
                 height=self.height,
                 phase_fraction=self.phase_fraction,
                 x0=self.x0,
                 feature=self.feature, # features don't need to be deep copied
                 text=self.text)
