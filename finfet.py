from v2 import *
oxide_thickness = 1
l1 = Layer(feature=Rectangle((100, 10)))
l2 = Layer(phase_fraction=0.45, feature=Rectangle((10, 20)))
l3 = Layer(feature=Rectangle((100, oxide_thickness)))
l4 = conformal_layer(l2, thickness=oxide_thickness)

d = Device()
d.stack(l1)
d.stack([l3, l4, l2])

g = pyxcolor.rgb(0.4, 0.4, 0.4)
y = pyxcolor.rgb(0.5, 0.5, 0)
k = pyxcolor.rgb.black
b = pyxcolor.rgb.blue
r = pyxcolor.rgb.red

colors = [k, r, r, k]

c = canvas.canvas()
for counter, l in enumerate(d):
    bbox = path.rect(*l.bbox)
    cl = canvas.canvas([canvas.clip(bbox)])
    for f in l:
        cl.fill(f.place(), [colors[counter]])
    c.insert(cl)

c.writeSVGfile('finfet')
gate_thickness = oxide_thickness

substrate = Layer(feature=Rectangle((100, 10)))
fin = Layer(x0=25, feature=Rectangle((50, 20)))
substrate_oxide = Layer(feature=Rectangle((100, oxide_thickness)))
fin_oxide = Layer(x0=25, feature=Rectangle((50, oxide_thickness)))
fin_gate = Layer(x0=35, feature=Rectangle((30, gate_thickness)))
n = Layer(x0=25, period=40, domain = (20,70), feature=Rectangle((10, 20)))  # source drain
fin_contacts = Layer(x0=20, period=55, feature=Rectangle(
            (5, 20 - oxide_thickness), y=oxide_thickness))
p = Layer(x0=35, feature=Rectangle((30, 20)))

d = Device()
d.stack(substrate)
d.stack([substrate_oxide, fin, n, fin_contacts, p])
d.stack(fin_oxide)
d.stack(fin_gate)

colors = [b, g, b, r, k, y, g, k]

c = canvas.canvas()
for counter, l in enumerate(d):
    bbox = path.rect(*l.bbox)
    cl = canvas.canvas([canvas.clip(bbox)])
    for f in l:
        cl.fill(f.place(), [colors[counter]])
    c.insert(cl)

c.writeSVGfile('finfet-alt')
