import doctest
import numpy
import sys


def is_vector(x):
    return isinstance(x, numpy.ndarray) and x.shape == (3,)


def normalize(vec):
    length = numpy.linalg.norm(vec)
    assert length > 1.e-10
    return (1. / length) * vec


def rotate(vec, axis, theta):
    axis = normalize(axis)
    vpar = numpy.dot(vec, axis) * axis
    u = vec - vpar
    um = numpy.linalg.norm(u)
    uhat = (1. / um) * u
    vhat = numpy.cross(axis, uhat)
    return vpar + (um * numpy.cos(theta)) * uhat + (um * numpy.sin(theta)) * vhat


class Line:
    """
    We can define a line in terms of its direction vector and any point known
    to lie on the line. It could also be two points.
    """
    def __init__(self, member, direction=None, second=None):
        if second is not None and is_vector(second):
            assert direction is None
            direction = second - member
        elif direction is not None and is_vector(direction):
            assert second is None
        else:
            raise Exception
        self.direction = direction
        self.member = member

    def __repr__(self):
        return "<Line {0} {1}>".format(self.member, self.direction)

    def intersect(self, other):
        if isinstance(other, Plane):
            return other.intersect(self)
        # intersect two lines - raise exception if they are not coplanar
        # or if they are parallel and not identical, if identical just return
        # either of them
        raise Exception("not implemented yet")


class Plane:
    """
    We can define a plane in terms of its normal vector and any point known
    to lie on the plane. It could also be a line and a point.
    """
    def __init__(self, member, normal=None, line=None):
        """
        """
        if line is not None and isinstance(line, Line):
            assert normal is None
            normal = numpy.cross(member - line.member, line.direction)
        elif normal is not None and is_vector(normal):
            assert line is None
        else:
            raise Exception
        self.normal = normalize(normal)
        self.member = member

    def intersect(self, other):
        if isinstance(other, Line):
            x0, n = self.member, self.normal
            x1 = other.member
            x2 = x1 + other.direction
            m = numpy.dot(x0 - x1, n) / numpy.dot(x2 - x1, n)
            return m * (x2 - x1) + x1
        elif isinstance(other, Plane):
            x1, x2 = self.member, other.member
            n1, n2 = self.normal, other.normal
            direction = normalize(numpy.cross(n1, n2))
            n1n2n1 = numpy.cross(direction, n1)
            m = numpy.dot(x2 - x1, n2) / numpy.dot(n1n2n1, n2)
            x = x1 + m * n1n2n1
            return Line(x, direction=direction)
        else:
            raise Exception


class StlFile:
    def __init__(self, vertices, paths):
        minx = miny = minz = 0.0
        for v in vertices:
            minx = min(minx, v[0])
            miny = min(miny, v[1])
            minz = min(minz, v[2])
        offset = numpy.array([-minx, -miny, -minz])
        self.vertices = map(lambda v: v + offset, vertices)
        self.paths = paths

    def dump(self):
        print "solid Foo"
        for p in self.paths:
            points = []
            verts = []
            for index in p:
                point = self.vertices[index]
                points.append(point)
                verts.append((25.4 * point[0], 25.4 * point[1], 25.4 * point[2]))
            n = normalize(numpy.cross(points[1] - points[0], points[2] - points[1]))
            v0 = verts[0]
            for i in range(1, len(verts) - 1):
                # Assume each surface is simple convex for now.
                print "    facet normal {0:e} {1:e} {2:e}".format(n[0], n[1], n[2])
                print "        outer loop"
                print "            vertex {0:e} {1:e} {2:e}".format(v0[0], v0[1], v0[2])
                print "            vertex {0:e} {1:e} {2:e}".format(verts[i][0], verts[i][1], verts[i][2])
                print "            vertex {0:e} {1:e} {2:e}".format(verts[i+1][0], verts[i+1][1], verts[i+1][2])
                print "        endloop"
                print "    endfacet"
        print "endsolid Foo"


# Dimensions of front surface
A = 22
B = 14
C = 5
dx = B / numpy.tan(numpy.pi / 3)

# The front surface
w = numpy.array([0, 0, 0])
x = numpy.array([dx, B, 0])
y = numpy.array([A + dx, B, 0])
z = numpy.array([A, 0, 0])
front_normal = normalize(numpy.cross(w - x, y - x))

theta = (-2./3) * numpy.pi
xy_side_normal = rotate(front_normal, y - x, theta)
yz_side_normal = rotate(front_normal, z - y, theta)
zw_side_normal = rotate(front_normal, w - z, theta)
wx_side_normal = rotate(front_normal, x - w, theta)

xy_side_plane = Plane(x, normal=xy_side_normal)
yz_side_plane = Plane(y, normal=yz_side_normal)
zw_side_plane = Plane(z, normal=zw_side_normal)
wx_side_plane = Plane(w, normal=wx_side_normal)

bottom = Plane(numpy.array([0, 0, -C]),
               normal=numpy.array([0, 0, 1]))

s = zw_side_plane.intersect(wx_side_plane).intersect(bottom)
t = wx_side_plane.intersect(xy_side_plane).intersect(bottom)
u = xy_side_plane.intersect(yz_side_plane).intersect(bottom)
v = yz_side_plane.intersect(zw_side_plane).intersect(bottom)

stl = StlFile(
    (w, x, y, z, s, t, u, v),
    (
        (3, 2, 1, 0),
        (4, 5, 6, 7),
        (1, 5, 4, 0),
        (2, 6, 5, 1),
        (3, 7, 6, 2),
        (0, 4, 7, 3)
    )
)

stl.dump()