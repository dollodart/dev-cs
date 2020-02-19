from devcs import *
from colors import devcolors as dc

substrate = Layer(feature = Rectangle((100,10)),color=dc['silicon'])
n = Layer(period=60, height=1, feature = Rectangle((40,1)),color=dc['n-type'])
p = Layer(x0=40, height=1, feature = Rectangle((20,1)),color=dc['p-type'])
oxide = Layer(feature=Rectangle((100,1)),color=dc['oxide'])
gate = Layer(x0=40, height=1, feature = Rectangle((20,1)),color=dc['gate'])

s = Schematic(wrap = 3)
d = Device()
d.stack(substrate)
s.stack(d.copy())
d.stack([n,p])
s.stack(d.copy())
d.stack(oxide)
s.stack(d.copy())
d.stack(gate)
s.stack(d)
s.write('mosfet',clip=False)
