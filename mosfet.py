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

s = Schematic(wrap = 10)
d = Device()
d.stack([substrate,n,p])
s.stack(d)

# not about copying
#e = d.copy()
#for l in e:
#    for f in l:
#        print(f.x,f.y)
#
s.write('a')
e2 = Device()
e2.stack([substrate.copy(),n.copy(),p.copy()])
for l in e2:
    for f in l:
        print(f.x,f.y)

s.stack(e2)
#f = Device()
#f.stack([substrate,n,p])
#f.stack(oxide)
#f.stack(gate)
#s.stack(f)
s.write('b')
