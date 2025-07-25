import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from parser import GerberParser
from transformer import ScaleTransformer
from plotter import CombinedGeometryPlotter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from exporter import DXFExporter, Pdf_Exporter

class GeometryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gerber Parser & Scaler")
        self.geometry("800x600")

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.cmds = []
        self.file_path = tk.StringVar()
        self.scale_x_var = tk.StringVar(value="1.0")
        self.scale_y_var = tk.StringVar(value="1.0")
        self.scaledPoints = []
        self._build_ui()

    def _build_ui(self):
        frm = ttk.Frame(self, padding=10)
        frm.grid(row=0, column=0, sticky='nsew')

        frm.rowconfigure(3, weight=1)
        for i in range(4):
            frm.columnconfigure(i, weight=1)

        ttk.Label(frm, text="Gerber File:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(frm, textvariable=self.file_path, width=60).grid(row=0, column=1, padx=5)
        ttk.Button(frm, text="Browse", command=self._select_file).grid(row=0, column=2)
        
        ttk.Label(frm, text="Scale X:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(frm, textvariable=self.scale_x_var, width=8).grid(row=1, column=1, sticky=tk.W)
        ttk.Label(frm, text="Scale Y:").grid(row=1, column=2, sticky=tk.W)
        ttk.Entry(frm, textvariable=self.scale_y_var, width=8).grid(row=1, column=3, sticky=tk.W)

        ttk.Button(frm, text="Run", command=self._run).grid(row=2, column=1, columnspan=2, pady=10)
        ttk.Button(frm, text="Export DXF", command=self._export_dxf).grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(frm, text="Export PDF", command=self._export_pdf).grid(row=2, column=3, sticky="W")

        self.mst = frm

    def _select_file(self):
        path = filedialog.askopenfilename(
            title="Select Gerber",
            filetypes=(("Gerber Files", ("*.gbr","*.GTL","*.GBR","*.GTP")), ("All Files","*.*"))
        )
        if path:
            self.file_path.set(path)

    def _run(self):
        path = self.file_path.get()
        if not path:
            messagebox.showwarning("No file", "Please choose a Gerber file first.")
            return

        try:
            sx = float(self.scale_x_var.get())
            sy = float(self.scale_y_var.get())
        except ValueError:
            messagebox.showerror("Invalid scale", "Scale X and Y must be numbers.")
            return

        parser = GerberParser(path)
        orig_cmds = parser.run()
        transformer = ScaleTransformer(sx, sy)
        self.cmds = orig_cmds
        orig_geom, scaled_geom, scaled_apts = transformer.apply(orig_cmds, [])
        self.scaledPoints = scaled_geom

        fig = Figure(figsize=(6, 6))
        ax = fig.add_subplot(111)
        plotter = CombinedGeometryPlotter(orig_geom, scaled_geom, ax=ax)
        plotter.plot()
        ax.invert_yaxis()

        canvas = FigureCanvasTkAgg(fig, master=self.mst)
        canvas.draw()
        canvas.get_tk_widget().grid(row=3, column=0, columnspan=4, sticky='nsew')

        toolbar_frame = ttk.Frame(self.mst)
        toolbar_frame.grid(row=4, column=0, columnspan=4, sticky='ew')
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()

    def _export_dxf(self):
        output_filename = filedialog.asksaveasfilename(
            defaultextension=".dxf",
            filetypes=(("DXF Files", "*.dxf"), ("All Files", "*.*")),
            title="Save DXF File"
        )
        if output_filename:
            try:
                exp = DXFExporter(self.scale_x_var.get(), self.scale_y_var.get(), output_filename, self.cmds)
                exp.export()
                messagebox.showinfo("Success", f"DXF file exported to: {output_filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Error exporting DXF: {e}")

    def _export_pdf(self):
        Pdf_Exporter(self.master, self.scaledPoints)

if __name__ == "__main__":
    app = GeometryApp()
    app.mainloop()
