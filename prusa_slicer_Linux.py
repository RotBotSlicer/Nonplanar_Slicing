import subprocess

# Slices a given STL-File planar in prusa slicer
# ----------------------------------------
# Input: target: STL-File path (string), profile: INI-File path (string), userParameters: additional paramters (string)
# Output: None
def sliceSTL(target, profile, userParameters, userPath="/usr/bin/"):
    filename = "output.gcode"
    prusa_slicer_path = fr'"{userPath}prusa-slicer"'
    command = f'{prusa_slicer_path} --export-gcode {target} --output {filename} --load {profile} {userParameters}'
    print(command)
    subprocess.run(command, shell=True)

# Repairs any faults in the STL-Facet normals
# ----------------------------------------
# Input: target: STL-File path (string)
# Output: None
def repairSTL(target):
    command = f'PrusaSlicer --export-stl {target} --repair --loglevel 0 --output {target}'
    print(command)
    subprocess.run(command, shell=True,stdout=subprocess.DEVNULL,
    stderr=subprocess.STDOUT)

# Opens the given STL-File in Prusa GCode-Viewer
# ----------------------------------------
# Input: target: GCode-File path (string)
# Output: None
def viewGCODE(target, userPath="/usr/bin/"):
    prusa_path = fr'"{userPath}prusa-slicer"'
    command = f"{prusa_path} {target}"
    print(command)
    subprocess.run(command, shell=True)