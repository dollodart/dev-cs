from numpy.linalg import norm
from numpy import array, roll, sqrt, argmin
from math import ceil, floor, nan, isnan
from pyx import path, canvas as pyxcanvas, color as pyxcolor, text, style
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
                 , devices_shift = []
                 , canvas = None):
        self.devices = devices
        self.wrap = wrap
        self.current_position = current_position
        self.devices_shift = devices_shift
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
        devl = self.place(0, 0)
        for cdev, devpath in enumerate(devl):
            for clay, laypath in enumerate(devpath):
                lay, laybbox = laypath
                laybbox_path = laybbox.to_path()
                laycanv = pyxcanvas.canvas()
                laycanv = pyxcanvas.canvas([
                    pyxcanvas.clip(laybbox_path)])
                feat = self.devices[cdev][clay].feature

                for cfea, feapath in enumerate(lay):
                    laycanv.fill(feapath, [feat.color])
                    laycanv.stroke(feapath, [feat.stroke_color])

                if self.devices[cdev][clay].text != '':
                    xc = (laybbox.x1+laybbox.x2)/2
                    yc = (laybbox.y1+laybbox.y2)/2
                    t = text.Text(self.devices[cdev][clay].text
                            , scale=2)
                    laycanv.text(xc,yc,t)

                self.canvas.insert(laycanv)

        self.canvas.writeEPSfile(filename)

    def write_ref(self, x1, y1, x2, y2):
        self.canvas.stroke(path.line(x1,y1,x2,y2), [style.linewidth.THICK])



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
            l.append(layer.place(x,
                y+self.stack_base[c],
                width=self.width))
        return l

    def __getitem__(self, i):
        return self.layers[i]

    def copy(self):
        layers = [layer.copy() for layer in self.layers]
        return Device(layers=layers,
                stack_height=self.stack_height,
                stack_base=self.stack_base,
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
            feats = ( (self.feature.place(x, y),), bbox)
            return feats
        fwidth = self.feature.get_width()
        # condition = (x + i*self.period + fwidth) / width < 1 + eps:
        # equivalently, i < ((1+eps)*width - fwidth - x)/self.period    
        n = ((1+eps)*width - x - fwidth) / self.period 
        n = ceil(n)
        #print(self.feature, n, width, (x + n*self.period + fwidth)/width)
        feats = tuple(self.feature.place(x + i*self.period,y) for i in range(n))
        return (feats, bbox)

    def copy(self):
        return self.__class__(
                 period=self.period,
                 height=self.height,
                 phase_fraction=self.phase_fraction,
                 x0=self.x0,
                 feature=self.feature, # features don't need to be deep copied
                 text=self.text)
