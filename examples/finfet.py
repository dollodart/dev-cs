from devcs import *
from colors import devcolors as dc
from conformal import conformal_coords

oxide_thickness = 1
substrate = Layer(feature=Rectangle(100, 10, color=dc['silicon']),text='substrate')
fin = Layer(feature=Rectangle(10, 20,color=dc['silicon']), x0 = 45, text='fin')
oxide = Layer(feature=Rectangle(100, oxide_thickness, color=dc['oxide']),text='oxide')

fin.feature.sort_coords()
fin_oxide = conformal_coords(fin.feature.coords, thx=oxide_thickness)
fin_oxide = ConvexPolygon(fin_oxide,color=dc['oxide'])
fin_oxide = Layer(feature=fin_oxide,x0=45,height=fin.height+oxide_thickness) 
#x0 pass does not require -thickness because conformal coords returns COP centered intrinsice feature coordinates, not lower left cornere assigned (0,0)
#may change
#height is specified to clip excess in the case of a tall feature
#feature clipping may be necessary for wide features

d = Device()
d.stack(substrate)
d.stack([oxide, fin_oxide, fin])
s = Schematic()
s.stack(d)
s.write('afinfet')

s = Schematic()
gate_thickness = oxide_thickness
substrate = Layer(feature=Rectangle(100, 10, color=dc['silicon']))
fin = Layer(feature=Rectangle(50, 20,color=dc['silicon']), x0 = 25)
substrate_oxide = Layer(feature=Rectangle(100, oxide_thickness, color=dc['oxide']))
fin_oxide = Layer(x0=25, feature=Rectangle(50, oxide_thickness, color=dc['oxide']))
fin_gate = Layer(x0=35, feature=Rectangle(30, gate_thickness, color=dc['gate']))
n1 = Layer(x0=25, feature=Rectangle(10, 20, color=dc['n-type']))  
n2 = Layer(x0=65, feature=Rectangle(10, 20, color=dc['n-type']))  
padlayer = Layer(feature=Square(oxide_thickness))
fin_contacts = Layer(x0=20, period=55, feature=Rectangle(5, 20-oxide_thickness,color=dc['contact']))
p = Layer(x0=35, feature=Rectangle(30, 20, color=dc['p-type']))

d2 = Device()
d2.stack(substrate)
d2.stack([substrate_oxide, fin, n1, n2, p, fin_contacts])
d2.stack_base[-1] += oxide_thickness
#d2.stack([substrate_oxide, fin, n1, n2, p])
#d2.stack_height += oxide_thickness - 20
#d2.stack(fin_contacts)
#d2.stack_height -= oxide_thickness
d2.stack(fin_oxide)
d2.stack(fin_gate)

s.stack(d2)

s.write('bfinfet')
