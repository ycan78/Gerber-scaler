from commands import GerberCommand, FlashCommand,RegionCommand,DrawCommand, ArcCommand
from apertures import ApertureDefinition
from geometry import Geometry, GeoAperture, GeoRegion, GeoDraw, GeoArc
class ScaleTransformer:
    def __init__(self, sx, sy):
        self.sx, self.sy = sx, sy

    def apply(self,
              original_cmds,
              original_apertures
             ):
        original_geometries=[]
        for cmd in original_cmds:
            if isinstance(cmd, FlashCommand):
                geom = GeoAperture(cmd)
            elif isinstance(cmd, RegionCommand):
                geom = GeoRegion(cmd)
            elif isinstance(cmd, DrawCommand):
                geom = GeoDraw(cmd)
            elif isinstance(cmd, ArcCommand):
                geom = GeoArc(cmd, last_pt)
            else:
                continue
            geom.command_to_geometry()
           
           
            original_geometries.append(geom)

        scaled_apts = {
        
        }
        scaled_geometries = []
                
        if self.sx!=1 and self.sy!=1:
            for geom in original_geometries:
                geom_scaled = geom.clone()
                geom_scaled.scale_geometry(self.sx, self.sy)
                scaled_geometries.append(geom_scaled)
        else:
            scaled_geometries=original_geometries    
        return original_geometries, scaled_geometries, scaled_apts
