from abc import ABC, abstractmethod
from typing import List, Tuple
from apertures import ApertureDefinition
from shapely.geometry import Polygon
import copy

                          
#Module for storing gerber commands


class GerberCommand(ABC):
    @abstractmethod
    def scale(self, sx, sy):
        
        ...

    def clone(self):
        
        return copy.deepcopy(self)

    @abstractmethod
    def to_gerber(self):
        ...

    def findPerpendicular(self, polygon,i):
        myPolygon=Polygon(polygon)
        myvector=np.array(polygon[i+1]-polygon[i])
        np.rot90(myvector)
        if (polygon[i+1]+(myvector.x,myvector.y)).within(myPolygon):
            myvector=-myvector
        return myvector    


class FlashCommand(GerberCommand):
    def __init__(self, x, y, aperture):
        self.x = x
        self.y = y
        self.aperture = aperture

    def scale(self, sx, sy):
        
        self.aperture = self.aperture.scale(sx, sy)

    def to_gerber(self):
        return f"X{self.x:.6f}Y{self.y:.6f}D03*"

class DrawCommand(GerberCommand):
    def __init__(self, path, aperture):
        self.path     = list(path)
        self.aperture = aperture
        self.mode     = 'draw'  

    def scale(self, sx, sy):
        if not self.path:
            return

        new_path = []
        
        x0, y0 = self.path[0]
        new_path.append((x0 + sx, y0 + sy))

        
        for (xp, yp), (x, y) in zip(self.path, self.path[1:]):
            dx, dy = x - xp, y - yp
            nx = new_path[-1][0] + dx 
            ny = new_path[-1][1] + dy 
            new_path.append((nx, ny))

        self.path     = new_path
        self.aperture = self.aperture.scale(sx, sy)

    def to_gerber(self):
        op = '1' if self.mode == 'draw' else '2'
        x, y = self.path[-1]
        return f"X{x:.6f}Y{y:.6f}D0{op}*"

class RegionCommand(GerberCommand):
    def __init__(self, polygon):
        self.polygon = list(polygon)

    def scale(self, sx, sy):
        if not self.polygon:
            return

        new_poly = []
        
        x0, y0 = self.polygon[0]
        new_poly.append((x0 + sx*0.1, y0 + sy*0.1))

        
        for (xp, yp), (x, y) in zip(self.polygon, self.polygon[1:]):
            dx, dy = x - xp, y - yp
            nx = new_poly[-1][0] + dx
            ny = new_poly[-1][1] + dy
            new_poly.append((nx, ny))

        self.polygon = new_poly

    def to_gerber(self):
        body = "\n".join(f"X{x:.6f}Y{y:.6f}D01*" for x, y in self.polygon)
        return f"G36*\n{body}\nG37*"


class ArcCommand(GerberCommand):
    def __init__(self,
                 end,
                 i_off,
                 j_off,
                 clockwise,
                 aperture):
        self.end = end
        self.center_offset = (i_off, j_off)
        self.clockwise = clockwise
        self.aperture = aperture

    def scale(self, sx, sy):
        
        ex, ey = self.end
        ix, iy = self.center_offset
        cx, cy = ex - ix, ey - iy
        
        i2, j2 = ix*sx, iy*sy
        self.center_offset = (i2, j2)
        
        self.end = (cx + i2, cy + j2)
        
        self.aperture = self.aperture.scale(sx, sy)

    def to_gerber(self):
        code = 'G02' if self.clockwise else 'G03'
        ex, ey = self.end
        i2, j2 = self.center_offset
        return f"{code}X{ex:.6f}Y{ey:.6f}I{i2:.6f}J{j2:.6f}D01*"
