from v2 import *
substrate = Layer(feature = Rectangle((100,10)))
n = Layer(period = 60, height=10, feature = Rectangle((40,1),y=8.9))
p = Layer(x0=40, height=10, feature = Rectangle((20,1),y=8.9))
oxide = Layer(feature=Rectangle((100,1)))
gate = Layer(x0=40, height=10, feature = Rectangle((20,1)))

d = Device()
d.stack([substrate,n,p])
d.stack(oxide)
d.stack(gate)

g = pyxcolor.rgb(0.4,0.4,0.4)
y = pyxcolor.rgb(0.5,0.5,0)
k = pyxcolor.rgb.black
b = pyxcolor.rgb.blue
r = pyxcolor.rgb.red

colors = [b,r,y,g,k]

c = canvas.canvas()
for counter,l in enumerate(d):
    bbox = path.rect(*l.bbox)
    cl = canvas.canvas([canvas.clip(bbox)])
    for f in l:
        cl.fill(f.place(),[colors[counter]])
    c.insert(cl)

c.writeSVGfile('mosfet')

s = Schematic()
s.stack(d)
s.write()
