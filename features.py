from pyx import path, color as pyxcolor
from numpy import sqrt, arctan2, array, roll
from numpy.linalg import norm

class Bbox():
    """A bounding box. One definition of a bounding box in common use is the tuple (x1,y1,x2,y2) where 
    x1 is the x-coordinate of the lower left corner (the minimum x)
    y1 is the y-coordinate of the lower left corner (the minimum y)
    x2 is the x-coordinate of the upper right corner (the maximum x)
    y2 is the y-coordinate of the upper right corner (the maximum y)
    """

    def __init__(self,x1,y1,x2,y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def __getitem__(self,i):
        if i == 0:
            return self.x1
        elif i == 1:
            return self.y1
        elif i == 2:
            return self.x2
        elif i == 3:
            return self.y2
        else:
            raise IndexError("Out of range")

    def __setitem__(self,i,v):
        if i == 0:
            self.x1 = v
        elif i == 1:
            self.y1 = v
        elif i == 2:
            self.x2 = v
        elif i == 3:
            self.y2 = v
    def __str__(self):
       return '{} {} {} {}'.format(self.x1,self.y1,self.x2,self.y2)

class PolygonFeature():
    # size is actually point coordinates
    def __init__(self, color=pyxcolor.rgb.black,stroke_color=pyxcolor.rgb.black):
        self.color = color
        self.stroke_color = stroke_color

    def sort_coords(self):
        phis = []
        xp, yp = zip(*self.coords)
        cop = (sum(xp) / len(xp), sum(yp) / len(yp))
        for point in self.coords:
            phis.append(arctan2(point[1] - cop[1], point[0] - cop[0]))
        s, s_phis = zip(*sorted(zip(self.coords, phis), key=lambda x: -x[1]))
        self.coords = s

    def place(self,x,y):
        paths = [path.moveto(x, y)]
        for point in self.coords:
            paths.append(path.lineto(x + point[0], y + point[1]))
        paths.append(path.closepath())
        return path.path(*paths)

    def get_bbox(self,x,y):
        """Return bbox based off the subclass coordinates.""" 
        xc, yc = zip(*self.coords)
        bbox = Bbox(min(xc) + x
                , min(yc) + y
                , max(xc) + x
                , max(yc) + y)
        return bbox

    def get_width(self):
        xc, _ = zip(*self.coords)
        return max(xc) - min(xc)

    def get_height(self):
        _, yc = zip(*self.coords)
        return max(yc) - min(yc)



class Square(PolygonFeature):
    def __init__(self, a, color=pyxcolor.rgb.black,stroke_color=pyxcolor.rgb.black):
        super().__init__(color=color,stroke_color=stroke_color)
        self.char_dims = a
        self.coords = [ (0,0)
                        , (a, 0)
                        , (a, a)
                        , (0, a) ]

class Rectangle(PolygonFeature):
    def __init__(self, w, h, color=pyxcolor.rgb.black,stroke_color=pyxcolor.rgb.black):
        super().__init__(color=color,stroke_color=stroke_color)
        self.char_dims = (w, h)
        self.coords = [ (0,0)
                        , (w, 0)
                        , (w, h)
                        , (0, h) ]

class RightTriangleUpBack(PolygonFeature):
    def __init__(self, a, b, color=pyxcolor.rgb.black,stroke_color=pyxcolor.rgb.black):
        super().__init__(color=color,stroke_color=stroke_color)
        self.char_dims = (a,b)
        self.coords = [ (0,0)
                        , (a,0) 
                        , (0,b)]

class RightTriangleUpForward(PolygonFeature):
    def __init__(self, a, b, color=pyxcolor.rgb.black,stroke_color=pyxcolor.rgb.black):
        super().__init__(color=color,stroke_color=stroke_color)
        self.char_dims = (a,b)
        self.coords = [ (0,0)
                        , (a,0) 
                        , (a,b)]

class RightTriangleDownForward(PolygonFeature):
    def __init__(self, a, b, color=pyxcolor.rgb.black,stroke_color=pyxcolor.rgb.black):
        super().__init__(color=color,stroke_color=stroke_color)
        self.char_dims = (a,b)
        self.coords = [ (a,0)
                        , (a,b) 
                        , (0,b)]

class RightTriangleDownBack(PolygonFeature):
    def __init__(self, a, b, color=pyxcolor.rgb.black,stroke_color=pyxcolor.rgb.black):
        super().__init__(color=color,stroke_color=stroke_color)
        self.char_dims = (a,b)
        self.coords = [ (0,0)
                        ,(a,b)
                        ,(0,b)
                        ]

#all possibilities: 
#- (0,0), (a,0), (0,b) 
#- (0,0), (a,0), (a,b)
#- (a,0), (a,b), (0,b)
#- (0,0), (a,b), (0,b)

class EquilateralTriangle(PolygonFeature):
    def __init__(self, a, color=pyxcolor.rgb.black,stroke_color=pyxcolor.rgb.black):
        super().__init__(color=color,stroke_color=stroke_color)
        self.char_dims = a 
        self.coords = [ (0,0)
                        , (a/2, a*sqrt(3)/2)
                        , (a, 0) ]

class ConvexPolygon(PolygonFeature):
    def __init__(self, coords, color=pyxcolor.rgb.black,stroke_color=pyxcolor.rgb.black):
        super().__init__(color=color,stroke_color=stroke_color)
        self.char_dims = coords
        self.coords = coords
        self.sort_coords()

#non-linear 
#class Semicircle(Feature):
#    def __init__(self, size, x=0, y=0):
#        super().__init__(size, x, y)
#        self.r = self.size/2.
#        self.bbox = Bbox(x, y, x + 2 * self.r, y + self.r)
#
#    def place(self,x,y):
#        return path.path(
#            path.arc(
#                x + self.x +
#                self.r,
#                y + self.y,
#                self.r,
#                0,
#                180),
#            path.lineto(
#                x + self.x +
#                2 *
#                self.r,
#                y + self.y))
#
#    def magnify(self, thickness):
#        """for non-linear shapes"""
#        magnification = 1 + thickness/self.r
#        self.x += (1 - magnification) * self.r
#        self.r *= magnification
