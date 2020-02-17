from pyx import path

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

class Feature:
    """

    x: the x-coordinate of the lower left corner of the feature
    y: the y-coordinate of the lower left corner of the feature
    size: a scalar, list of scalars, or list of coordinates which determines the feature size (and sometimes shape) for subclasses

    """
    def __init__(self, size, x, y):
        self.size = size
        self.x = x
        self.y = y

    def copy(self):
        return self.__class__(size=self.size, x=self.x, y=self.y)

class Square(Feature):

    def __init__(self, size, x=0, y=0):
        super().__init__(size, x, y)
        self.l = self.size
        self.bbox = Bbox(x, y, self.x + self.l, self.y + self.l)

    def place(self,x,y):
            self.x = x
            self.y =y 
            xll = self.x
            yll = self.y
            w = h = self.l
            return path.rect(xll, yll, w, h)

    def magnify(self, magnification):
        self.x += (1 - magnification) * self.l / 2
        self.l *= magnification


class Rectangle(Feature):
    def __init__(self, size, x=0, y=0):
        super().__init__(size, x, y)
        self.w = self.size[0]
        self.h = self.size[1]
        self.bbox = Bbox(x, y, self.x + self.w, self.y + self.h)

    def place(self,x,y):
        """Places the feature lower left and returns a path object describing the feature perimeter."""
#        return path.rect(self.x, self.y, self.w, self.h)
        return path.rect(x,y,self.w,self.h)

    def magnify(self, thickness):
        """Magnifies the feature to have a layer thickness greater while keeping the center."""
        mw = 1 + 2 * thickness / self.w
        mh = 1 + 2 * thickness / self.h
        self.x -= (mw - 1) * self.w / 2
        self.y -= (mh - 1) * self.h / 2
        self.w *= mw
        self.h *= mh


class Semicircle(Feature):
    def __init__(self, size, x=0, y=0):
        super().__init__(size, x, y)
        self.r = self.size
        self.bbox = Bbox(x, y, x + 2 * self.r, y + self.r)
        self.w = 2*self.r

    def place(self,x,y):
        self.x = x
        self.y = y
        return path.path(
            path.arc(
                self.x +
                self.r,
                self.y,
                self.r,
                0,
                180),
            path.lineto(
                self.x +
                2 *
                self.r,
                self.y))

    def magnify(self, thickness):
        magnification = 1 + thickness/self.r
        self.x += (1 - magnification) * self.r
        self.r *= magnification
        self.w = 2*self.r


class RightTriangleUp(Feature):
    def __init__(self, size, x=0, y=0):
        super().__init__(size, x, y)
        self.w = self.size[0]
        self.h = self.size[1]
        self.bbox = Bbox(x, y, x + self.w, y + self.h)

    def place(self,x,y):
        self.x = x
        self.y = y
        return path.path(path.moveto(self.x, self.y),
                         path.lineto(self.x + self.w, self.y + self.h),
                         path.lineto(self.x + self.w, self.y),
                         path.lineto(self.x, self.y))


class EquilateralTriangle(Feature):
    def __init__(self, size, x=0, y=0):
        super().__init__(size, x, y)
        self.a = self.size
        self.bbox = Bbox(x, y, x + self.a, y + self.a*sqrt(3)/2)

    def place(self,x,y):
        self.x = x
        self.y = y
        return path.path(path.moveto(self.x, self.y),
                         path.lineto(self.x + self.a/2,
                                     self.y + self.a*sqrt(3)/2),
                         path.lineto(self.x + self.a, self.y),
                         path.closepath())

    def magnify(self, magnification):
        self.x += (1 - magnification) * self.a / 2
        self.a *= magnification


class Polygon(Feature):
    # size is actually point coordinates
    def __init__(self, size, x=0, y=0):
        super().__init__(size, x, y)
        phis = []
        xp, yp = zip(*size)
        cop = (sum(xp) / len(xp), sum(yp) / len(yp))
        for point in size:
            phis.append(arctan2(point[1] - cop[1], point[0] - cop[0]))
        s, s_phis = zip(*sorted(zip(size, phis), key=lambda x: -x[1]))
        self.bbox = Bbox(x, y, x + max(xp), y + max(yp))
        self.s = s

    def place(self,x,y):
        self.x = x
        self.y = y
        paths = [path.moveto(self.x, self.y)]
        for point in self.s:
            paths.append(path.lineto(self.x + point[0], self.y + point[1]))
        paths.append(path.closepath())
        return path.path(*paths)

    def magnify(self, thickness):
        delta = thickness
        rs = array(self.size)

        cop = rs.mean(axis=0)
        rs = rs - cop
        ds = rs - roll(rs, 1, axis=0)
        ds = (ds.T / norm(ds, axis=1)).T
        a = ds - roll(ds, -1, axis=0)
        a = (a.T/norm(a, axis=1)).T
        d = (a.T*delta*norm(rs, axis=1)).T
        rsp = rs + d
        self.s = rsp + cop
