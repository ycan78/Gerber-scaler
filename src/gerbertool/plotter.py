import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from geometry import GeoAperture, GeoRegion, GeoDraw, GeoArc
from commands import FlashCommand, DrawCommand, RegionCommand, ArcCommand

class CombinedGeometryPlotter:
    def __init__(self,
                 original_geometries,
                 scaled_geometries=None,
                 ax=None,
                 figsize=(8, 8)):
        
        self.orig_geom   = original_geometries or []
        self.scaled_geom = scaled_geometries or []

        if ax is not None:
    
            self.ax  = ax
            self.fig = ax.figure
        else:

            self.fig, self.ax = plt.subplots(figsize=figsize)
            self.ax.invert_yaxis()

    def plot(self):
        
        
        self.ax.cla()
        self.ax.set_aspect('equal', 'box')
        self.ax.invert_yaxis()

        def draw(geometries, color, linestyle, linewidth, label):
            color_dict={'C': 'red', 'O': 'orange', 'R': 'green', 'ROUNDRECT': 'purple', 'RR': 'purple', "MACRO": "red"}
            last_pt = None
            color_temp=color
            for geom in geometries:
                if isinstance(geom,GeoAperture):
                    
                    color=color_dict[geom.cmd.aperture.shape]
    
                
                pts = geom.points
                if pts is None or len(pts) == 0:
                    continue

                if isinstance(geom, (GeoAperture, GeoRegion)):
                    patch = MplPolygon(
                        pts, closed=True,
                        fill=False,
                        edgecolor=color,
                        linestyle=linestyle,
                        linewidth=linewidth,
                        label=label
                    )
                    self.ax.add_patch(patch)
                else:
                    xs, ys = pts[:,0], pts[:,1]
                    self.ax.plot(
                        xs, ys,
                        color=color,
                        linestyle=linestyle,
                        linewidth=linewidth,
                        label=label
                    )
                color=color_temp
                
                label = None
                last_pt = (pts[-1,0], pts[-1,1])

        
        draw(self.orig_geom,  color='grey', linestyle='-', linewidth=1.0, label='Original')
        
        draw(self.scaled_geom, color='black', linestyle='--',  linewidth=0.5, label='Scaled')

        
        self.ax.relim()
        self.ax.autoscale_view()
        self.ax.legend(loc='upper right')

        
        if plt.fignum_exists((8,8)):

            plt.show()
