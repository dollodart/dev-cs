from devcs import *

g = pyxcolor.rgb(0.4,0.4,0.4)
y = pyxcolor.rgb(0.5,0.5,0)
k = pyxcolor.rgb.black
b = pyxcolor.rgb.blue
r = pyxcolor.rgb.red

substrate = Layer(feature = Rectangle((100,10)),color=b)
n = Layer(period = 60, height=10, feature = Rectangle((40,1),y=8.9),color=r)
p = Layer(x0=40, height=10, feature = Rectangle((20,1),y=8.9),color=y)
oxide = Layer(feature=Rectangle((100,1)),color=g)
gate = Layer(x0=40, height=10, feature = Rectangle((20,1)),color=k)

d = Device()
d.stack([substrate,n,p])
d.stack(oxide)
d.stack(gate)
s = Schematic()
s.stack(d)
s.write('mosfet')
