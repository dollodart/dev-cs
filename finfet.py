from devcs import *
g = pyxcolor.rgb(0.4, 0.4, 0.4)
y = pyxcolor.rgb(0.5, 0.5, 0)
k = pyxcolor.rgb.black
b = pyxcolor.rgb.blue
r = pyxcolor.rgb.red

oxide_thickness = 1
substrate = Layer(feature=Rectangle((100, 10)), color=b,text='substrate')
fin = Layer(feature=Rectangle((10, 20)), phase_fraction = 0.45, color=b,text='fin')
oxide = Layer(feature=Rectangle((100, oxide_thickness)), color=g,text='oxide')

fin_oxide = conformal_layer(fin, thickness=oxide_thickness)
fin_oxide.color = g
fin.stroke = False

d = Device()
d.stack(substrate)
d.stack([oxide, fin_oxide, fin])
s = Schematic()
s.stack(d)
s.write('afinfet')
import sys
sys.exit()

gate_thickness = oxide_thickness
substrate = Layer(feature=Rectangle((100, 10)), color=b)
fin = Layer(feature=Rectangle((50, 20)), x0 = 25, color=b)
substrate_oxide = Layer(feature=Rectangle((100, oxide_thickness)), color=g)
fin_oxide = Layer(x0=25, feature=Rectangle((50, oxide_thickness)), color=g)
fin_gate = Layer(x0=35, feature=Rectangle((30, gate_thickness)), color=k)
n = Layer(x0=25, period=40, domain=(20, 70),
          feature=Rectangle((10, 20)), color=r)  # source drain
fin_contacts = Layer(x0=20, period=55, feature=Rectangle(
    (5, 20 - oxide_thickness), y=oxide_thickness), color=k)
p = Layer(x0=35, feature=Rectangle((30, 20)), color=y)

d2 = Device()
d2.stack(substrate)
d2.stack([substrate_oxide, fin, n, fin_contacts, p])
d2.stack(fin_oxide)
d2.stack(fin_gate)

s.stack(d2)

s.write('bfinfet2',clip=False)
