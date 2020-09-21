from devcs import *
from pyx import color as pyxcolor

f = Semicircle(3)
l = Layer(feature=f,period=30)
d = Device()
f, x0 = f.magnify(0.05)
f.color = f.stroke_color = pyxcolor.rgb.red
l2 = Layer(feature=f,period=30,x0=x0)
d.stack((l2,l))

s = Schematic()
s.stack(d)
s.write('non-lin')
