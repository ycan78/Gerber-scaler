import re
from gerbonara.aperture_macros.parse import ApertureMacro as GBApertureMacro
                                                                
#Module for storing gerber apertures

class ApertureDefinition:
    def __init__(self, code, shape, params,units):
        self.code = code   
        self.shape = shape
        self.params = params
        self.units=units

    @staticmethod
    def parse(line, units):
        pattern = re.compile(r'%ADD(\d+)([A-Za-z]*),([^*]+)\*%')


        conversion_factor = 1.0
   
        if units == 'inches' or units=="in":
            conversion_factor = 25.4
    
        converted_params=[]
        m=pattern.match(line)
        if m:
            num = int(m.group(1))
            shape = m.group(2)
            params_str = m.group(3)
            if 'X' in params_str:
                raw_sizes = map(float, params_str.split('X'))
            else:
                raw_sizes = map(float, params_str.split())


            for size in raw_sizes:
                converted_params.append(size * conversion_factor)

            return ApertureDefinition(num,shape,converted_params, units)

        

    
    @staticmethod
    def from_macro(code, macro, params, units):
        inst = ApertureDefinition(code, 'MACRO', params, units)
        inst.macro      = macro
        inst.params     = params
        return inst
       
    def scale(self, sx, sy):
        if self.shape == 'MACRO':
            
            new_params = [p * sx for p in self.params]
            inst = ApertureDefinition.from_macro(self.code, self.macro, new_params, self.units)
            return inst


      
        if self.shape == 'C':
            
            d = self.params[0]
            return ApertureDefinition(self.code, 'O', [d*sx, d*sy])
        elif self.shape == 'R':
            w, h = self.params[:2]
            return ApertureDefinition(self.code, 'R', [w*sx, h*sy])
        elif self.shape == 'O':
            L, W = self.params[:2]
            return ApertureDefinition(self.code, 'O', [L*sx, W*sy])
        elif self.shape == 'P':
            
            diam = self.params[0] * sx
            rest = self.params[1:]
            return ApertureDefinition(self.code, 'P', [diam] + rest)
        else:
            
            return ApertureDefinition(self.code,
                                      self.shape,
                                      [p*sx for p in self.params])
        


