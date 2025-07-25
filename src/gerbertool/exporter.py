import tkinter as tk
import ezdxf
from tkinter import ttk, filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle, Circle as MplCircle, Polygon as MplPolygon,PathPatch, Ellipse
import numpy as np
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import mm as rl_mm
from reportlab.lib import colors
from geometry import GeoAperture, GeoRegion, GeoDraw, GeoArc
from transformer import ScaleTransformer
from reportlab.lib.pagesizes import A4
import matplotlib.pyplot as plt



class DXFExporter:
    
    def __init__(self, scale_x, scale_y, filename, commands):
        self.sx = float(scale_x)
        self.sy = float(scale_y)
        self.filename = filename
        self.commands = commands

    def export(self):
        
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()

        
        transformer = ScaleTransformer(self.sx, self.sy)
        _, scaled_geoms, _ = transformer.apply(self.commands, {})

        for geom in scaled_geoms:
            
            if isinstance(geom, GeoAperture):
                geo = geom
            elif isinstance(geom, GeoDraw):
                geo = geom
            elif isinstance(geom, GeoRegion):
                geo = geom
            elif isinstance(geom, GeoArc):
                geo = geom
            else:
                continue

            pts = geo.command_to_geometry()
            if pts is None or len(pts) == 0:
                continue

            
            coords = [(float(x), float(y)) for x, y in pts]
            
            close = isinstance(geo, (GeoAperture, GeoRegion)) or np.allclose(pts[0], pts[-1])
            msp.add_lwpolyline(coords, close=close)

        doc.saveas(self.filename)
        print(f"DXF saved to {self.filename}")






class Pdf_Exporter(tk.Toplevel):
    def __init__(self,master, geoms):
        super().__init__(master)
        self.title("PDF exporter")
        self.geometry("900x900")
        self.config(bg="#f0f0f0")

        self.geoms=geoms  
        self.bbox=[]  
        self.translate_x_offset_mm=tk.DoubleVar(value=0.0)  
        self.translate_y_offset_mm=tk.DoubleVar(value=0.0)  
        self.fiducial_offset_percent=tk.DoubleVar(value=80)  
        self.fiducial_positions=[]  

        self.fig, self.ax=plt.subplots(figsize=(9,9))  
        self.canvas=FigureCanvasTkAgg(self.fig, master=self)  
        self.canvas_widget=self.canvas.get_tk_widget()  


        self._create_widgets()  

        self._initial_preview()  

    def _create_widgets(self):  
        control_frame=tk.Frame(self, bg="#f0f0f0", bd=2, relief=tk.RAISED)  
        control_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)  

        tk.Label(control_frame, text="Translate X (mm):", bg="#f0f0f0").pack(side=tk.LEFT, padx=5, pady=5)  
        tk.Entry(control_frame, textvariable=self.translate_x_offset_mm,width=10).pack(side=tk.LEFT, padx=5, pady=5)  
        self.translate_x_offset_mm.trace_add("write", lambda *args: self._update_preview())  




        tk.Label(control_frame, text="Translate Y (mm)", bg="#f0f0f0").pack(side=tk.LEFT, padx=5, pady=5)  
        tk.Entry(control_frame, textvariable=self.translate_y_offset_mm, width=10).pack(side=tk.LEFT, padx=5, pady=5)  
        self.translate_y_offset_mm.trace_add("write", lambda *args: self._update_preview)  

        tk.Label(control_frame, text="Fiducial Offset (%):", bg="#f0f0f0").pack(side=tk.LEFT, padx=5, pady=5)  
        tk.Entry(control_frame, textvariable=self.fiducial_offset_percent, width=10).pack(side=tk.LEFT, padx=5, pady=5)  
        self.fiducial_offset_percent.trace_add("write", lambda *args: self._update_preview())  

        tk.Button(control_frame, text="Export Final Pdf", command=self._export_final_pdf).pack(side=tk.RIGHT, padx=5, pady=5)  

        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)  

        self.toolbar= NavigationToolbar2Tk(self.canvas, self)  
        self.toolbar.update  
        self.canvas_widget.pack()
      
    def _update_preview(self):
        self.ax.clear()
        self.ax.set_aspect('equal', adjustable='box')

        
        page_w_pts, page_h_pts = landscape(A4)
        page_w_mm = page_w_pts / rl_mm
        page_h_mm = page_h_pts / rl_mm

        margin_mm = 10.0
        drawable_w = page_w_mm  - 2*margin_mm
        drawable_h = page_h_mm  - 2*margin_mm

        
        a4 = Rectangle((0,0), page_w_mm, page_h_mm, fill=False, edgecolor='blue')
        self.ax.add_patch(a4)

        
        all_pts = []
        for geom in self.geoms:
            pts = getattr(geom, 'points', None)
            if pts is None or len(pts)==0:
                continue
            all_pts.append(pts)
        if not all_pts:
            self.canvas.draw_idle()
            return

        combined = np.vstack(all_pts)
        min_x, min_y = combined.min(axis=0)
        max_x, max_y = combined.max(axis=0)
        geom_w = max_x - min_x
        geom_h = max_y - min_y

        
        geom_w = geom_w if geom_w>0 else 1.0
        geom_h = geom_h if geom_h>0 else 1.0

        
        scale_x = drawable_w / geom_w
        scale_y = drawable_h / geom_h
        pdf_scale = min(scale_x, scale_y)

        
        tx = margin_mm - min_x * pdf_scale + self.translate_x_offset_mm.get()
        ty = margin_mm - min_y * pdf_scale + self.translate_y_offset_mm.get()

        
        for geom in self.geoms:
            pts = getattr(geom, 'points', None)
            if pts is None or len(pts)==0:
                continue

            
            pts_t = pts * pdf_scale + np.array([tx, ty])

            if isinstance(geom, (GeoAperture, GeoRegion)):
                patch = MplPolygon(pts_t, closed=True,
                                   facecolor='black', edgecolor='black', linewidth=1)
                self.ax.add_patch(patch)
            else:
                
                xs, ys = pts_t[:,0], pts_t[:,1]
                self.ax.fill(xs, ys, facecolor='black', edgecolor='black', linewidth=1)

        
        self.ax.set_xlim(0, page_w_mm)
        self.ax.set_ylim(0, page_h_mm)
        
        self.ax.set_title("Gerber Geometry Preview")
        self.ax.axis('off')
        self.canvas.draw_idle()

    def _initial_preview(self):  
        self._update_preview()   
  
    def render_geometry_to_canvas_reportlab(self, pdf_canvas_obj):
        pdf_canvas_obj.saveState()

        plot_margin_mm = 10.0

        
        all_pts = []
        for geo in self.geoms:
            pts = getattr(geo, 'points', None)
            if pts is None or len(pts) == 0:
                continue
            all_pts.append(pts)
        if not all_pts:
            pdf_canvas_obj.restoreState()
            return

        combined = np.vstack(all_pts)
        min_x_geom, min_y_geom = combined.min(axis=0)
        max_x_geom, max_y_geom = combined.max(axis=0)

        
        geom_w = (max_x_geom - min_x_geom) or 0.1
        geom_h = (max_y_geom - min_y_geom) or 0.1

        
        tx_mm = plot_margin_mm - min_x_geom + self.translate_x_offset_mm.get()
        ty_mm = plot_margin_mm - min_y_geom + self.translate_y_offset_mm.get()
        pdf_canvas_obj.translate(tx_mm * rl_mm, ty_mm * rl_mm)
        pdf_canvas_obj.scale(rl_mm, rl_mm)

        
        pad = 10.0
        bg_x = min_x_geom - pad
        bg_y = min_y_geom - pad
        bg_w = geom_w + 2 * pad
        bg_h = geom_h + 2 * pad
        pdf_canvas_obj.setFillColor(colors.black)
        pdf_canvas_obj.rect(bg_x, bg_y, bg_w, bg_h, fill=1)

        
        pdf_canvas_obj.setStrokeColor(colors.white)
        pdf_canvas_obj.setFillColor(colors.white)
        pdf_canvas_obj.setLineWidth(0.00025)

        for geo in self.geoms:
            pts = getattr(geo, 'points', None)
            if pts is None or len(pts) == 0:
                continue

            if pts.shape[0] > 1:
                path = pdf_canvas_obj.beginPath()
                path.moveTo(pts[0, 0], pts[0, 1])
                for x, y in pts[1:]:
                    path.lineTo(x, y)

                do_fill = False
                if np.allclose(pts[0], pts[-1]) and pts.shape[0] > 2:
                    path.close()
                    do_fill = True
                pdf_canvas_obj.drawPath(path, stroke=1, fill=do_fill)

            else:
                x, y = pts[0]
                pdf_canvas_obj.circle(x, y, 0.1, fill=1, stroke=0)


        fiducial_radius_mm = 1.0
    
        center_x_geom = min_x_geom + (geom_w / 2.0)
        center_y_geom = min_y_geom + (geom_h / 2.0)

        offset_x = (geom_w / 2.0) * (float(self.fiducial_offset_percent.get()) / 100.0)
        offset_y = (geom_h / 2.0) * (float(self.fiducial_offset_percent.get()) / 100.0)

        fiducial_positions = [
        (center_x_geom - offset_x, center_y_geom - offset_y),
        (center_x_geom + offset_x, center_y_geom - offset_y),
        (center_x_geom + offset_x, center_y_geom + offset_y),
        (center_x_geom - offset_x, center_y_geom + offset_y)
        ]

        pdf_canvas_obj.setFillColor(colors.white)
        for fx, fy in fiducial_positions:
            pdf_canvas_obj.circle(fx, fy, fiducial_radius_mm, fill=1, stroke=0)

        pdf_canvas_obj.restoreState()
       
    def export_scaled_geometry_to_pdf(self, filename):  
        pdf_canvas_obj=canvas.Canvas(filename, pagesize=landscape(A4))  

        self.render_geometry_to_canvas_reportlab(pdf_canvas_obj)  


        try:  
            pdf_canvas_obj.showPage()  
            pdf_canvas_obj.save()  
        except Exception as e:  
            print(f"Error exporting PDF file {e}")  

    def _export_final_pdf(self):  
        filename=filedialog.asksaveasfilename(  
            parent=self,  
            defaultextension="pdf",  
            filetypes=(("PDF FILES", "*pdf"), ("All Files", "*.*")),  
            title="Save Pdf File"  
        )  
        if filename:  
            try:  
                self.export_scaled_geometry_to_pdf(filename)  

                messagebox.showinfo("Succes", f"PDF file exported to {filename}", parent=self)  
            except Exception as e:  
                messagebox.showerror("Error", f"Error exporting Pdf: {e}", parent=self)