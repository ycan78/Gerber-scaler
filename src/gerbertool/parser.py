import re
from commands import GerberCommand, FlashCommand, DrawCommand, RegionCommand, ArcCommand
from apertures import ApertureDefinition
import gerbonara.aperture_macros.parse as gp

class GerberParser:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.lines= []
        self.units = 'mm'
        self.zero_suppression = 'leading'
        self.int_digits= 2
        self.frac_digits= 4
        self.divisor= 10 ** self.frac_digits
        self.coord_mode= 'absolute'

        self.apertures= {}
        self.macro_defs= {}
        self.macro_params={}
        self.commands= []

    def load_file(self):
        with open(self.filepath, 'r') as f:
            self.lines = [ln.strip() for ln in f if ln.strip()]


    def _split_commands(self, data):
        text = '\n'.join(data) if isinstance(data, list) else data


        for match in re.finditer(r'G04.*?\*\s*|%.*?%\s*|[^*%]*\*\s*', text, re.DOTALL):
            cmd = match[0]
            newlines = cmd.count('\n')
            cmd = cmd.strip().strip('%').rstrip('*')
            if cmd:
                
                
                yield cmd
            
    
        



    def detect_units(self):
        for line in self.lines:
            if '%MOIN*' in line or line.startswith('G70'):
                self.units = 'inches'
            elif '%MOMM*' in line or line.startswith('G71'):
                self.units = 'mm'

    def parse_format(self):
  
        fs_re = re.compile(r'%FS([LT])([AI])X(\d)(\d)Y(\d)(\d)\*%')
        mo_re = re.compile(r'%MO(IN|MM)\*%')
        for line in self.lines:
            m = fs_re.match(line)
            if m:
                self.zero_suppression = 'leading' if m.group(1)=='L' else 'trailing'
                self.coord_mode      = 'absolute'  if m.group(2)=='A' else 'incremental'
                self.int_digits_x    = int(m.group(3))
                self.frac_digits_x   = int(m.group(4))
                self.int_digits_y    = int(m.group(5))
                self.frac_digits_y   = int(m.group(6))
                self.div_x = 10 ** self.frac_digits_x
                self.div_y = 10 ** self.frac_digits_y
            m2 = mo_re.match(line)
            if m2:
                self.units = 'in' if m2.group(1)=='IN' else 'mm'




    def parse_macro_definitions(self):
   
        import gerbonara.aperture_macros.parse as gp
        NAME = r"[a-zA-Z_$\.][a-zA-Z_$\.0-9+\-]+"
        am_start=re.compile(fr"AM(?P<name>{NAME})\*(?P<macro>[^%]*)")
        i = 0
        for line in self._split_commands(self.lines):
            m = am_start.match(line)
            if m:
                i += 1
                self.macro_params[m['name']]=m.group('macro') 
                macro = gp.ApertureMacro.parse_macro(m['name'],m['macro'], self.units)
                self.macro_defs[m['name']] = macro
            i += 1

    def parse_apertures(self):
        add_re = re.compile(r'%ADD(\d+)([A-Za-z0-9_]+)(?:,([^*]+))?\*%')

        for line in self.lines:
            m = add_re.match(line)
            if not m:
                continue
            code   = int(m.group(1))
            name   = m.group(2)
            param_str = m.group(3) or ''
            if name in self.macro_defs:
                
                if param_str=='':
                    vals=[]
                else:
                    vals=[ float(val) for val in param_str.strip(' ,').split('X') ]

                if self.units == 'in':
                    vals = [v * 25.4 for v in vals]
                aperture = ApertureDefinition.from_macro(code, self.macro_defs[name], vals, self.units)
            else:
                aperture = ApertureDefinition.parse(line, units=self.units)
            self.apertures[code] = aperture


    def _parse_coord(self, raw):
        neg = raw.startswith('-')
        if neg:
            raw = raw[1:]

        total = self.int_digits + self.frac_digits
        if self.zero_suppression == 'leading':
            s = raw.rjust(total, '0')
        else:
            s = raw.ljust(total, '0')

        int_part  = s[:self.int_digits] if self.int_digits else '0'
        frac_part = s[self.int_digits:] if self.frac_digits else ''

        val = int(int_part)
        if self.frac_digits:
            val += int(frac_part) / float(10 ** self.frac_digits)
        return -val if neg else val

    def _extract_xy(self, xs, ys):
        
        if self.zero_suppression == 'leading':
            xs = xs.zfill(self.int_digits_x + self.frac_digits_x)
            ys = ys.zfill(self.int_digits_y + self.frac_digits_y)
        else:
            xs = xs.ljust(self.int_digits_x + self.frac_digits_x, '0')
            ys = ys.ljust(self.int_digits_y + self.frac_digits_y, '0')

        x = int(xs) / self.div_x
        y = int(ys) / self.div_y

        
        if self.units == 'in':
            x *= 25.4
            y *= 25.4

        return x, y


    def parse_commands(self):

        flash_re = re.compile(r'^(?:G01)?X([-+]?\d+)Y([-+]?\d+)D03\*$')
        draw_re  = re.compile(r'^(?:G01)?X([-+]?\d+)Y([-+]?\d+)D0([12])\*$')
        arc_re   = re.compile(r'^G0([23])X([-+]?\d+)Y([-+]?\d+)I([-+]?\d+)J([-+]?\d+)\*$')
        region_on  = re.compile(r'^G36\*$')
        region_off = re.compile(r'^G37\*$')
        tool_re  = re.compile(r'^(?:G5[04])?D(\d+)\*$')
        move_re        = re.compile(r'^(?:G0?1)?X([-+]?\d+)Y([-+]?\d+)D02\*$')
        move_x_only    = re.compile(r'^(?:G0?1)?X([-+]?\d+)D02\*$')
        move_y_only    =re.compile(r'^(?:G0?1)?Y([-+]?\d+)D02\*$')
        flash_xy_re    = re.compile(r'^(?:G0?1)?X([-+]?\d+)Y([-+]?\d+)D03\*$')
        flash_only_re  = re.compile(r'^D03\*$')
        last_x = None
        last_y = None


        
        self.commands = []
        current_ap = None
        in_region  = False
        region_pts = []

        for line in self.lines:

            if line.startswith('G04'):
                continue

            if line == 'M02*':
                continue
            m = move_re.match(line)
            if m:
                
                last_x, last_y = self._extract_xy(m.group(1), m.group(2))

                continue
            else: 
                m=move_x_only.match(line)
                if m:
                    last_x, _ =self._extract_xy(m.group(1), '0')
     
                m=move_y_only.match(line)
                if m:
                    _, last_y= self._extract_xy('0', m.group(1))
                    


            m = flash_xy_re.match(line)
            if m and current_ap:
                x, y = self._extract_xy(m.group(1), m.group(2))
                last_x, last_y = x, y
                

                self.commands.append(FlashCommand(x, y, current_ap))
               
                continue
            if flash_only_re.match(line) and current_ap and last_x is not None:
                self.commands.append(FlashCommand(last_x, last_y, current_ap))
                

                continue

            m = tool_re.match(line)
            if m:
                
                code = int(m.group(1))
                current_ap = self.apertures.get(code)
                continue


            if region_on.match(line):
                in_region  = True
                region_pts = []
                continue
            if region_off.match(line):
                self.commands.append(RegionCommand(region_pts.copy()))
                in_region = False
                continue


            if in_region:
                m = draw_re.match(line)
                if m:
                    x, y = self._extract_xy(m.group(1), m.group(2))
                    region_pts.append((x, y))
                continue


            m = flash_re.match(line)
            if m and current_ap:
                x, y = self._extract_xy(m.group(1), m.group(2))
                self.commands.append(FlashCommand(x, y, current_ap))

   
                continue


            m = draw_re.match(line)
            if m and current_ap:
                x, y = self._extract_xy(m.group(1), m.group(2))
                mode = 'draw' if m.group(3) == '1' else 'move'
                cmd  = DrawCommand([(x, y)], current_ap)
                cmd.mode = mode
                self.commands.append(cmd)
                continue


            m = arc_re.match(line)
            if m and current_ap:
                cw = (m.group(1) == '2')
                x, y = self._extract_xy(m.group(2), m.group(3))
                i, j = self._extract_xy(m.group(4), m.group(5))
                self.commands.append(ArcCommand((x, y), i, j, cw, current_ap))
                continue

    def run(self):
        self.load_file()
        self.detect_units()
        self.parse_format()
        self.parse_macro_definitions()
        self.parse_apertures()
        self.parse_commands()
        return self.commands