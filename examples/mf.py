from devcs import *
from colors import devcolors as dc

substrate = Layer(feature = Rectangle(100,10,color=dc['silicon']))
n = Layer(period=60, feature = Rectangle(40,1,color=dc['n-type']))
p = Layer(x0=40, feature = Rectangle(20,1,color=dc['p-type']))
oxide = Layer(feature=Rectangle(100,1,color=dc['oxide']))
gate = Layer(x0=40, feature = Rectangle(20,1,color=dc['gate']))

d = Device()
d.stack(substrate)
d.stack([n,p])
d.stack(oxide)
d.stack(gate)
s = Schematic()
s.stack(d)
s.write('mosfet')
