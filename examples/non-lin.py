from devcs import *
from pyx import color as pyxcolor
from convfuncs import num2period_half

s = Schematic()
d = Device()
f = Semicircle(3)
p, x0 = num2period_half(10, f.get_width(), d.width)
l = Layer(period=p, feature=f, x0=x0, height=1)
f, x0a = f.magnify(0.05)
f.color = f.stroke_color = pyxcolor.rgb.red
l2 = Layer(feature=f, period=p, x0=x0 + x0a, height=1)

d.stack((l2, l))

s.stack(d)
s.write('non-lin')
