import filereader
import numpy as np
import surface
import gcode_transform_1

stl_pfad = "Welle.stl"
triangle_array = filereader.openSTL(stl_pfad)
Oberflaeche = surface.create_surface(triangle_array, np.pi / 3) # Winkel

path_gcode = "C:/Users/zuerc/Documents/Informatik_Projekte/PA/PA23_wuem_346_Nonplanar/output.gcode"
gcode_raw = filereader.openGCODE(path_gcode)
gcode_transform_1.trans_gcode(gcode_raw, Oberflaeche)

# -> x, y und z vektoren mit den zugehoerigen e und f- Werten in ein Array schreiben
# -> Offset des GCodes erkennen, resp. bei X und Y = 0 slicen?
# -> jeder G1 Code separat mit griddata dauert zu lange -> ganze Schicht zusammen in Griddata
# -> Alle Daten in np Array speichern fuer performance
# -> 

