# Gerber-scaler

A GUI application for parsing, visualizing, scaling, and exporting Gerber PCB files.

## Features

- **Parse** RS-274X Gerber files
- **Visualize** original and scaled geometry in an interactive plot
- **Scale** by custom X/Y factors
- **Export** to DXF and PDF (preserving proportions)
- **Standalone executable**: no Python or dependencies required on user’s machine

##  Download

Get the latest standalone executable from  [Releases page](https://github.com/ycan78/Gerber-scaler/releases):

- **Linux** (ELF): `app`
- **Windows** (EXE): `app.exe`

> Ensure the file is executable on Linux:
>
> ```bash
> chmod +x app
> ```

## Usage

1. **Run the application**
   ```bash
   ./app
   ```
2. **Open a gerber file**
-Click Browse, select your .gbr file, then click Run.
-The original geometry will appear in the plot.
3. **Scale the plot**
-Enter X and Y scale factors
-Click run again to see both scaled and orginal geometry
4. **Export**
-DXF: Click Export DXF to save a CAD-ready file.
-PDF:Click Export PDF to generate a proportional PDF.

## Installation from Source
If you prefer to build from source, ensure you have Python 3.8+ and dependencies:
```bash
git clone https://github.com/ycan78/Gerber-scaler.git
cd Gerber-scaler
pip install -r requirements.txt
cd source/gerbertool
python3 app.py
```
## License
Released under the MIT License. See LICENSE for full details.



