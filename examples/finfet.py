from devcs import *
from colors import devcolors as dc

oxide_thickness = 1
substrate = Layer(feature=Rectangle((100, 10)), color=dc['silicon'],text='substrate')
fin = Layer(feature=Rectangle((10, 20)), phase_fraction = 0.45, color=dc['silicon'],text='fin')
oxide = Layer(feature=Rectangle((100, oxide_thickness)), color=dc['oxide'],text='oxide')

fin_oxide = conformal_layer(fin, thickness=oxide_thickness)
fin_oxide.color = dc['oxide']
fin.stroke = False

d = Device()
d.stack(substrate)
d.stack([oxide, fin_oxide, fin])
s = Schematic()
s.stack(d)
s.write('afinfet',clip=True)

gate_thickness = oxide_thickness
substrate = Layer(feature=Rectangle((100, 10)), color=dc['silicon'])
fin = Layer(feature=Rectangle((50, 20)), x0 = 25, color=dc['silicon'])
substrate_oxide = Layer(feature=Rectangle((100, oxide_thickness)), color=dc['oxide'])
fin_oxide = Layer(x0=25, feature=Rectangle((50, oxide_thickness)), color=dc['oxide'])
fin_gate = Layer(x0=35, feature=Rectangle((30, gate_thickness)), color=dc['gate'])
n = Layer(x0=25, period=40, domain=(20, 75),
          feature=Rectangle((10, 20)), color=dc['n-type'])  # source drain
fin_contacts = Layer(x0=20, period=55, feature=Rectangle(
    (5, 20 - oxide_thickness), y=oxide_thickness), color=dc['contact'])
p = Layer(x0=35, feature=Rectangle((30, 20)), color=dc['p-type'])

d2 = Device()
d2.stack(substrate)
d2.stack([substrate_oxide, fin, n, fin_contacts, p])
d2.stack(fin_oxide)
d2.stack(fin_gate)

s.stack(d2)

s.write('bfinfet',clip=True)
