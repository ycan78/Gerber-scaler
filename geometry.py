import numpy as np
import copy
from abc import ABC, abstractmethod
from shapely.geometry import Point, LineString, Polygon, box
from gerbonara.graphic_primitives import Circle, ArcPoly, Line, Arc,Rectangle
import math


class Geometry(ABC):
    def __init__(self):
        
        self.points: np.ndarray = np.empty((0, 2))

    def __iter__(self):
        return iter(self.points)
    def clone(self):
        
        return copy.deepcopy(self)
    
    @abstractmethod
    def command_to_geometry(self):
        pass

    @abstractmethod
    def find_center(self):
        pass

    def findPerpendicular(self, points, i, eps= 1e-8):
        pts = np.asarray(points)
        N = len(pts)
        if N < 3:
            return np.zeros(2)

        
        coords = pts.tolist()
        if not np.allclose(pts[0], pts[-1]):
            coords.append(coords[0])
        poly = Polygon(coords)

        
        prev = pts[(i-1) % N]
        curr = pts[i % N]
        nxt  = pts[(i+1) % N]

        edge = nxt - prev
        perp = np.array([-edge[1], edge[0]])
        norm = np.linalg.norm(perp)
        if norm < eps:
            return np.zeros(2)
        dir = perp / norm

        
        candidate = curr + dir
        return dir if Point(*candidate).within(poly) else -dir

    def scale_geometry(self, scale_x, scale_y):
 
        if self.points is None:
            return

 
        pts = self.points
        N = len(pts)
        if N < 3:
            return

        new_pts = pts.copy()
        for i in range(N):
            perp = self.findPerpendicular(pts, i)
            offset = np.array([
                -perp[0] * (scale_x-1),
                -perp[1] * (scale_y-1),
            ])
            new_pts[i] = pts[i] + offset

        self.points = new_pts

class GeoAperture(Geometry):
    def __init__(self, cmd):

        self.cmd = cmd
        self.shape = cmd.aperture.shape.upper()
        self.params = cmd.aperture.params
        self.center = np.array([cmd.x, cmd.y])
        self.points = None

    def command_to_geometry(self):
        
        u = np.array([1.0, 0.0])  
        v = np.array([0.0, 1.0])
        num_pts = 128
        ap = self.cmd.aperture
        if ap.shape == 'MACRO':
      
            
            shapes = ap.macro.to_graphic_primitives(
                offset=(self.cmd.x,self.cmd.y),
                rotation=0,
                parameters=ap.params,
                unit='mm',
                polarity_dark=True
            )
            all_pts = []
            for prim in shapes:
                
     
                if isinstance(prim, Circle):
         
                    theta = np.linspace(0, 2*math.pi, 64, endpoint=False)
                    x = prim.x + prim.r * np.cos(theta)
                    y = prim.y + prim.r * np.sin(theta)
                    coords = np.column_stack([x, y])

                
                elif isinstance(prim, ArcPoly):
                    coords = np.array(prim.outline)

                
                elif isinstance(prim, Line):
   
                    coords = np.array([[prim.x1, prim.y1],
                                       [prim.x2, prim.y2]])

                
                elif isinstance(prim, Arc):

                    cx = prim.x1 + prim.cx
                    cy = prim.y1 + prim.cy
                    r  = math.hypot(prim.x1 - cx, prim.y1 - cy)
                    a1 = math.atan2(prim.y1 - cy, prim.x1 - cx)
                    a2 = math.atan2(prim.y2 - cy, prim.x2 - cx)
                    
                    if prim.clockwise:
                        if a2 > a1: a2 -= 2*math.pi
                        angles = np.linspace(a1, a2, 32)
                    else:
                        if a2 < a1: a2 += 2*math.pi
                        angles = np.linspace(a1, a2, 32)
                    x = cx + r * np.cos(angles)
                    y = cy + r * np.sin(angles)
                    coords = np.column_stack([x, y])

                
                elif isinstance(prim, Rectangle):

                    poly = prim.to_arc_poly()
                    coords = np.array(poly.outline)

                else:
                
                    continue

                all_pts.append(coords)

            
            self.points=np.vstack(all_pts)
            return np.vstack(all_pts)



        if self.shape == 'C':
                  
            r = self.params[0] / 2
            angles = np.linspace(0, 2*np.pi, num_pts, endpoint=False)
            pts = np.stack([r*np.cos(angles), r*np.sin(angles)], axis=1)
        elif self.shape =='E':

            L, W = self.params[:2]
            angles = np.linspace(0, 2*np.pi, num_pts, endpoint=False)
            pts = np.stack([(L/2)*np.cos(angles), (W/2)*np.sin(angles)], axis=1)
        elif self.shape == 'R':       
            w, h = self.params[:2]
        
  
            corners = np.array([
                [-w/2, -h/2],
                [ w/2, -h/2],
                [ w/2,  h/2],
                [-w/2,  h/2],
                [-w/2, -h/2],  
            ])
            
            pts = []
            sides = [(corners[i], corners[i+1]) for i in range(4)]
            segs = num_pts//4
            for a,b in sides:
                pts.append(np.linspace(a, b, segs, endpoint=False))
            pts = np.vstack(pts)
        elif self.shape =='D':
            w, h= self.params[:2]
            chamfer=self.params[2]
            corners=np.array([
                [-w/2,0],
                [0, -h/2],
                [w/2, 0],
                [0, h/2],
                [-w/2,0]
            ])
            chamfer_pts=[]
            pts_per_edge= n_points//4
            for i in range(4):
                p1=corners[i]
                p2=corners[(i+1)%4]


                edge_vec=p2-p1
                edge_len= np.linalg.norm(edge_vec)
                unit_vec= edge_vec/ edge_len


                start= p1+ unit_vec*chamfer
                end= p2-unit_vec*chamfer


                t=np.linspace(0,1,pts_per_edge, endpoint=False)
                edge_pts= start[None, :] + (end-start)[None, :] * t[:, None]
                chamfer_pts.append(edge_pts)

            pts=np.vstack(chamfer_pts)
        elif self.shape =="CR":
            w, h= self.params[:2]
            chamfer=self.params[2]
            corners=np.array([
                [-w/2, -h/2],
                [ w/2, -h/2],
                [ w/2,  h/2],
                [-w/2,  h/2],
                [-w/2, -h/2],
            ])
            chamfer_pts=[]
            pts_per_edge= n_points//4
            for i in range(4):
                p1=corners[i]
                p2=corners[(i+1)%4]


                edge_vec=p2-p1
                edge_len= np.linalg.norm(edge_vec)
                unit_vec= edge_vec/ edge_len


                start= p1+ unit_vec*chamfer
                end= p2-unit_vec*chamfer


                t=np.linspace(0,1,pts_per_edge, endpoint=False)
                edge_pts= start[None, :] + (end-start)[None, :] * t[:, None]
                chamfer_pts.append(edge_pts)

            pts=np.vstack(chamfer_pts)
        elif self.shape=='RR':
            w, h= self.params[:2]
            radius=self.params[2]
            corners=np.array([
                [-w/2, -h/2],
                [ w/2, -h/2],
                [ w/2,  h/2],
                [-w/2,  h/2],
                [-w/2, -h/2],
            ])
            
            pts = []
            sides = [(corners[i], corners[i+1]) for i in range(4)]
            segs = num_pts//4
            for a,b in sides:
                pts.append(np.linspace(a, b, segs, endpoint=False))
            pts = np.vstack(pts)
        elif self.shape == 'O':          
            L, W = self.params[:2]
            angles = np.linspace(0, 2*np.pi, num_pts, endpoint=False)
            pts = np.stack([(L/2)*np.cos(angles), (W/2)*np.sin(angles)], axis=1)
        elif self.shape== 'P':
            side=self.params[0]
            pts=np.vstack(pts)
   
        else:                            
            pts = np.zeros((1,2))

        
        self.points = pts.dot(np.stack([u,v]).T) + self.center
        return self.points

    def find_center(self):
        return self.center
   
class GeoRegion(Geometry):
    def __init__(self, cmd):
        
        self.points = np.array(cmd.polygon)
        self.center = None

    def command_to_geometry(self):
        return self.points

    def find_center(self):
        
        poly = Polygon(self.points)
        cx, cy = poly.centroid.x, poly.centroid.y
        self.center = np.array([cx, cy])
        return self.center
   
class GeoDraw(Geometry):
    def __init__(self, cmd):
        
        self.points = np.array(cmd.path)
        self.center = None

    def command_to_geometry(self):
        return self.points

    def find_center(self):
        
        x,y = self.points.T
        L = np.hypot(np.diff(x), np.diff(y))
        if L.sum() == 0:
            return self.points.mean(axis=0)
        mid = np.cumsum(L) - L/2
        idx = np.searchsorted(np.cumsum(L), L.sum()/2)
        self.center = self.points[idx]
        return self.center

class GeoArc(Geometry):
    def __init__(self, cmd, last_point):
        
        self.start = np.array(last_point)
        self.end   = np.array(cmd.end)
        self.off   = np.array(cmd.center_offset)
        self.clockwise = cmd.clockwise
        self.center = self.start + self.off
        self.points = None

    def command_to_geometry(self):
        r = np.linalg.norm(self.off)
        v0 = self.start - self.center
        v1 = self.end   - self.center
        e0 = np.arctan2(v0[1], v0[0])
        e1 = np.arctan2(v1[1], v1[0])
        
        if self.clockwise:
            if e1 > e0:
                e1 -= 2*np.pi
        else:
            if e1 < e0:
                e1 += 2*np.pi
        thetas = np.linspace(e0, e1, 64)
        self.points = np.stack([
            self.center[0] + r*np.cos(thetas),
            self.center[1] + r*np.sin(thetas)
        ], axis=1)
        return self.points

    def find_center(self):
        return self.center
