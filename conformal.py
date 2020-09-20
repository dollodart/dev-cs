import numpy as np
import numpy.linalg as la
R = np.array([[0, 1]
    ,[-1, 0]]) #need transpose?

def si_perp_bisec(pi,pip1):
    intercept = (pi + pip1)/2
    slope = R @ (pip1 - pi)
    return slope, intercept

def si_ang_bisec(pim1,pi,pip1):
    intercept = pi
    slope = 2*pi - pip1 - pim1
    return slope, intercept

def calc_intercept(slope1,intercept1,slope2,intercept2):
    coeff = np.array([slope1, -slope2]).transpose()
    inter = intercept2 - intercept1
    extent = la.solve(coeff, inter)
    # test that the equation was solved (solution should be exact)
    assert ( abs((extent[0]*slope1 + intercept1) - (extent[1]*slope2 + intercept2)) < 0.001 ).all()
    return extent[0]*slope1 + intercept1

def calc_cosine(a,b,c):
    """calculate the angle made between vectors 
    going from points b->a and b->c"""
    r1 = a - b
    r2 = c - b
    r1 = r1 / np.linalg.norm(r1)
    r2 = r2 / np.linalg.norm(r2)
    return np.dot(r1,r2) # returns the cosine of angle

def sort_verts(verts):
    centroid = verts.mean(axis=0)
    phis = [ np.arctan2(v[1] - centroid[1], v[0] - centroid[0]) for v in verts]
    return verts[np.argsort(phis)]

def conformal_coords(verts,thx=0.05,lowerleftorigin=False):
    """Create the coordinates of a conformal layer on a polygon.  Loops
    through the n vertices, at each vertex calculating the coordinates for the 
    half-edges to the perpendicular bisectors neighboring that vertex. """

    if type(verts) is list or type(verts) is tuple:
        verts = np.array(verts)

    centroid = verts.mean(axis=0)
    coords = []
    n = len(verts)
    for i in range(n): # there are actually n-1 edges
        pi = verts[i]
        pip1 = verts[(i+1) % n]
        pim1 = verts[i-1]
        abi_s,abi_i = si_ang_bisec(pim1,pi,pip1)
        j = 0
        for v in pim1, pip1: 
            pbi_s,pbi_i = si_perp_bisec(pi, v) 
            pai = calc_intercept(pbi_s,pbi_i,abi_s,abi_i)
            # test that the perpendicular bisector is closer to the intercept than the angular bisector
            assert la.norm(pbi_i - pai) < la.norm(abi_i - pai)
            # test that the slope vector is pointing outward, that is, away from the origin
            # dot product with radial vector at that point is positive
            if np.dot(pbi_s, pbi_i - centroid) < 0:
                pbi_s *= -1
            if np.dot(abi_s, abi_i - centroid) < 0:
                abi_s *= -1

            cost = calc_cosine(pbi_i,pai,abi_i)

            if j == 0:
                coords.append( pbi_i + pbi_s/np.linalg.norm(pbi_s)*thx )
                coords.append( abi_i + abi_s/np.linalg.norm(abi_s)*thx/cost )
            else:
                coords.append( abi_i + abi_s/np.linalg.norm(abi_s)*thx/cost )
                coords.append( pbi_i + pbi_s/np.linalg.norm(pbi_s)*thx )

            j += 1
    coords = np.array(coords)
    if lowerleftorigin:
        coords = coords - coords.min(axis=0)
    return np.array(coords)


if __name__ == '__main__':
    from pyx import canvas, path, color

    def vpaths(verts):
        paths = [path.moveto(verts[0][0], verts[0][1])] 
        for v in verts:
            paths.append(path.lineto(v[0], v[1]))
        paths.append(path.closepath())
        return path.path(*paths)
    c = canvas.canvas()
    # square
    #verts = np.array((
    #    (-1,1)
    #   ,(1,1)
    #   ,(1,-1)
    #   ,(-1,-1)
    #   )) # n-by-2

    ## isoceles triangle
    #verts = np.array((
    #    (0,0)
    #   ,(1,1)
    #   ,(2,0)
    #   ))
    
    ## equilateral triangle
    #verts = np.array((
    #    (0,0)
    #   ,(0.5,0.866)
    #   ,(1,0)
    #   ))

    ## scalene triangle
    verts = np.array((
        (0,0)
       ,(1.3,2.6)
       ,(1.4,-0.1)
       ))
    
    verts = sort_verts(verts) # assumes neighboring angle points are neighboring vertices
    # for highly irregular and non-convex polygons you must input the coordinates in sorted order
    # and there is no guarantee the algorithm will work
    cc = conformal_coords(verts)
    c.fill(vpaths(cc), [color.rgb.red])
    c.fill(vpaths(verts), [color.rgb.blue])
    c.writeEPSfile('ex.eps')
