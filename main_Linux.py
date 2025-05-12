# Import custom .py Files
import filereader as fr
import prusa_slicer_Linux as ps
import surface as sf
import transform_method_1 as tm1
import transform_method_2 as tm2
# Import official Librarys
import time
import os
import platform
import dearpygui.dearpygui as dpg       # install with pip: "pip install dearpygui"                 -> Version 1.10.0
import numpy as np                      # install with pip: "pip install numpy"                     -> Version 1.24.3
import scipy                            # install with pip: "python -m pip install scipy"           -> Version 1.11.1
import shapely                          # install with pip: "pip install shapely"                   -> Version 2.0.1

if __name__ == "__main__":

    # Setup Default Paths if nothing is marked
    stl_default = "test_files/Welle_klein.stl"
    config_default = "test_files/generic_config_Mini.ini"

    # Create the window with its Context
    dpg.create_context()

    # set default path for linux
    prusaslicer_default_path = '/usr/bin/'

    # Standard comment as path
    stl_dir = "C:/ "
    config_dir = "C:/ "

    stl_path_dir_default = stl_dir
    config_path_dir_default = config_dir

    # default Parameter definition
    max_angle_default = 40          # default value for visualisation
    outline_offset_default = 3.5    # in mm
    resolution_zmesh = 0.05
    outline_active = False          # default GUI visibility for the offset
    default_planar_baselayer = 2
    method2_upscale_iteration = 0
    transform_method = 'mirror'


    # Interupthandling if a button or similiar is activated
    def stl_chosen(sender, app_data, user_data):
        stl_dir = app_data["file_path_name"]
        dpg.set_value("checkbox_cad", False)
        dpg.set_value("stl_text", stl_dir)
        
    def config_chosen(sender, app_data, user_data):
        config_dir = app_data["file_path_name"]
        dpg.set_value("checkbox_config", False)
        dpg.set_value("config_text", config_dir)
        
    def slicer_chosen(sender, app_data, user_data):
        prusaslicer_default_path = app_data["file_path_name"]
        dpg.set_value("slicer_text", prusaslicer_default_path)
        
    def default_cad_path(sender, app_data, user_data):
        if app_data:
            stl_dir = stl_default
            dpg.set_value("stl_text", stl_dir)
        
    def default_config_path(sender, app_data, user_data):
        if app_data:
            config_dir = config_default
            dpg.set_value("config_text", config_dir)
            
    def case1_marked(sender, app_data, user_data):
        if app_data:
            dpg.set_value("checkbox_case2", False)
            dpg.hide_item("text_planar_baselayer")
            dpg.hide_item("planar_baselayer")
            dpg.hide_item("dropdown")
            dpg.hide_item("dropdown_text")
            dpg.show_item("checkbox_outline_offset")
            dpg.show_item("text_offset_value")
        else:
            dpg.set_value("checkbox_case1", True)
        
    def case2_marked(sender, app_data, user_data):
        if app_data:
            dpg.set_value("checkbox_case1", False)
            dpg.show_item("text_planar_baselayer")
            dpg.show_item("planar_baselayer")
            dpg.show_item("dropdown")
            dpg.show_item("dropdown_text")
            dpg.hide_item("checkbox_outline_offset")
            dpg.hide_item("text_offset_value")
        else:
            dpg.set_value("checkbox_case2", True)
            
    def outline_offset_marked(sender, app_data, user_data):
        if app_data:
            dpg.show_item("outline_offset_value")
        else:
            dpg.hide_item("outline_offset_value")
            
    def dropdown_callback(sender, app_data, user_data):
        if app_data:
            transform_method = app_data        
        
    def show_gcode_prusaslicer(sender, app_data, user_data):
        output_path = dpg.get_value("stl_text").rsplit('.')[0] + '.gcode'
        ps.viewGCODE(output_path, dpg.get_value("slicer_text"))
        
                
    def calculate_button(sender, app_data, user_data):
        # if the paths are changed to a custom one
        if dpg.get_value("stl_text") == stl_path_dir_default :
            stl_dir = stl_default
            dpg.set_value("stl_text", stl_dir)
            dpg.set_value("checkbox_cad", True)
        
        if dpg.get_value("config_text") == config_path_dir_default:
            config_dir = config_default
            dpg.set_value("config_text", config_dir)
            dpg.set_value("checkbox_config", True)
        
        dpg.set_value("showtext_calculate_button", "calculation started")
            
        max_angle = np.deg2rad(dpg.get_value('max_angle_input'))
        # Start with the calculation
        dpg.show_item("loading")
        
    # ---------------------------------Function for slicing etc. here ---------------------------------------
        if os.path.exists(dpg.get_value("slicer_text")+"prusa-slicer"):
            if dpg.get_value("checkbox_case1"):
                # Here goes the calculations for Case 1
                # Open the .stl to the triangle Array
                triangle_array = fr.openSTL(dpg.get_value("stl_text"))
                # Get the Config as String to determine the layerheight etc.
                config = fr.slicer_config(fr.openINI(dpg.get_value("config_text")))
                # Define PrintInfo for Layerheight infos etc.
                printSetting = tm1.PrintInfo(config,FullBottomLayers=4, FullTopLayers=4, resolution_zmesh = resolution_zmesh)
                # set new path for the resulting .gcode
                printSetting.path = dpg.get_value("stl_text").rsplit('.')[0] + '.gcode'
                # Calculate the Surface Array
                # Give Feedback on the current progress
                print("Calculating Surface Interpolation")
                if dpg.get_value("checkbox_outline_offset"): # Run this condition, when the offset in the GUI is true
                    # Create the surface 
                    Oberflaeche, limits = sf.create_surface(triangle_array, max_angle)
                    # Extract the contour (from the buildplate) and sort the points in the array
                    points_sorted = sf.sort_contour(triangle_array)
                    # Create an offset of the contour and apply it on the surface
                    surface_filtered = sf.offset_contour(points_sorted[:,0], points_sorted[:,1], Oberflaeche, dpg.get_value("outline_offset_value"))
                    # Create a 'nearest' interpolation of the whole meshgrid
                    xmesh, ymesh, zmesh = sf.create_surface_extended_case1(surface_filtered, limits, printSetting.resolution)
                    # Create a gradient mesh of the whole structure
                    gradx_mesh, grady_mesh, gradz = sf.create_gradient(Oberflaeche, limits)
                    
                else:
                    filtered_surface, limits = sf.create_surface(triangle_array, max_angle) # Winkel
                    # Calculate the nearest extrapolated points outside of the surface
                    xmesh, ymesh, zmesh = sf.create_surface_extended(filtered_surface, limits, printSetting.resolution)
                    # Calculate the gradient of the surface for extruding optimizing
                    gradx_mesh, grady_mesh, gradz = sf.create_gradient(filtered_surface, limits)




                start = time.time()

                
                # Transform the .stl for slicing
                transformed_stl = tm1.trans_stl(triangle_array, zmesh, limits, printSetting)

                timenow = time.time()
                print('STL file transformed in {:.2f}s'.format(timenow - start))
                startrepair = time.time()
                
                # write the .stl to a temp file
                temp_stl_path = fr.writeSTL(transformed_stl)
                # repair damaged triangles in the .stl (wrong surface direction -> normalvector wrong)
                ps.repairSTL(temp_stl_path)

                timenow = time.time()
                print('STL file repaired in {:.2f}s'.format(timenow - startrepair))
                print('STL file generated in {:.2f}s'.format(timenow - start))
                startslice = time.time()
                
                # Slice the transformed .stl
                ps.sliceSTL(temp_stl_path,dpg.get_value("config_text"),'--info', dpg.get_value("slicer_text"))

                timenow = time.time()
                print('STL file sliced in {:.2f}s'.format(timenow - startslice))
                startback = time.time()
                
                # Load the sliced and generated .gcode in an array
                orig_gcode, config = fr.openGCODE_keepcoms("output.gcode", get_config=True)
                # Transform the gcode according to the Surface
                tm1.trans_gcode(orig_gcode, gradz, zmesh,  printSetting, limits, config_string=config)

                timenow = time.time()
                print('GCode backtransformed in {:.2f}s'.format(timenow - startback))
                
                # Delete the temp generated .stl
                os.remove(temp_stl_path)
                os.remove('output.gcode')

                timenow = time.time()
                print('total time {:.2f}s'.format(timenow - start))
            
            if dpg.get_value("checkbox_case2"):
                
                start = time.time()
                
                # Repair stl to check for faults in the stl          
                ps.repairSTL(dpg.get_value("stl_text"))
                # Read STL to the orig_stl Array with Shape [NR_OF_TRIANGLES, 12]
                orig_stl = fr.openSTL(dpg.get_value("stl_text"))
                # Upscale the STL for higher accuracy of the Nodes from the STL
                upscaled_stl = sf.upscale_stl(orig_stl, method2_upscale_iteration)
                # Calculate the Surface
                surface, limits = sf.create_surface(upscaled_stl, max_angle)
                #Create the extended Surface with 'nearest' extrapolated mesh points
                xmesh, ymesh, zmesh = sf.create_surface_extended(surface, limits, resolution_zmesh)
                # Create an Array with the xmesh, ymesh and zmesh values
                filtered_surface = np.concatenate(([xmesh.flatten()],[ymesh.flatten()],[zmesh.flatten()]),axis=0).T
                # Read the GCode Config from the Config File
                ini_config = fr.slicer_config(fr.openINI(dpg.get_value("config_text")))
                # read the layer height from the Config
                layer_height = ini_config.get_config_param('layer_height')
                # calculate the offset for the desired planar baselayers
                planarBaseOffset = (dpg.get_value('planar_baselayer') + 1) * float(layer_height)

                timenow = time.time()
                print('STL file transformed in {:.2f}s'.format(timenow - start))
                startslice = time.time()
                
                # Slice the STL planar only for the baselayers
                ps.sliceSTL(dpg.get_value("stl_text"),dpg.get_value("config_text"),f'{"--skirts 2 --skirt-height 2 --skirt-distance 6"}', dpg.get_value("slicer_text"))

                timenow = time.time()
                print('STL file sliced in {:.2f}s'.format(timenow - startslice))
                startback = time.time()
                
                # Open the GCode to the Array
                planar_base_gcode, prusa_generated_config_planar = fr.openGCODE_keepcoms('output.gcode')
                # Extract the desired number of baselayer from the sliced GCode
                base_layer_gcode = fr.readBaseLayers(planar_base_gcode,dpg.get_value('planar_baselayer'))
                # Transform the STL to get a flat top (mirroring upside down)
                transformed_stl = tm2.projectSTL(stl_data=upscaled_stl,filtered_surface=filtered_surface,planarBaseOffset=0.0,method=transform_method)
                # Write the transformed Nodes as a STL
                temp_stl_path = fr.writeSTL(transformed_stl)
                # Repair the created transformed STL
                ps.repairSTL(temp_stl_path)
                # Slice the Transformed STL to get a GCode
                ps.sliceSTL(temp_stl_path,dpg.get_value("config_text"),'', dpg.get_value("slicer_text"))
                # Read the GCode to the Array with the used config
                planar_gcode, prusa_generated_config = fr.openGCODE_keepcoms('output.gcode')
                # Retransform the Gcode to get a flat bottom layer
                tm2.transformGCODE(planar_gcode, base_layer_gcode, dpg.get_value("stl_text"), planarBaseOffset,filtered_surface, prusa_generated_config, layer_height)

                timenow = time.time()
                print('GCode backtransformed in {:.2f}s'.format(timenow - startback))
                
                # Remove the created temp files for clean structure in the explorer
                os.remove(temp_stl_path)
                os.remove('output.gcode')
                os.remove('temp_gcode.gcode')
                
                timenow = time.time()
                print('total time {:.2f}s'.format(timenow - start))

            # finishing informations for the User
            dpg.hide_item("loading")
            dpg.set_value("showtext_calculate_button", "Finished Gcode ready")
            
        else:
            dpg.hide_item("loading")
            dpg.set_value("showtext_calculate_button", "Prusaslicer Executable couldn't be found in given directory!")
        

    # Here are the File dialog defined
    with dpg.file_dialog(directory_selector=False, show=False, callback=stl_chosen, id="stl_select", width=700 ,height=400):
        dpg.add_file_extension(".stl", color=(255, 255, 255, 255))
        
    with dpg.file_dialog(directory_selector=True, show=False, callback=slicer_chosen, id="slicer_select", width=700 ,height=400):
        dpg.add_file_extension("")
        
    with dpg.file_dialog(directory_selector=False, show=False, callback=config_chosen, id="slicer_config", width=700 ,height=400):
        dpg.add_file_extension(".ini", color=(255, 255, 255, 255))

    # Custom Window with the corresponding buttons etc.
    with dpg.window(label="GCode Transformation", width=1000, height=500):
        
        with dpg.group(horizontal=True):
            dpg.add_text("------------------------------------ Select Path -------------------------------------------------")
        # Select the CAD File
        with dpg.group(horizontal=True):
            dpg.add_text("default:", tag="text_default_cad")
            dpg.add_checkbox(label="    ", callback=default_cad_path, tag="checkbox_cad")
            
            dpg.add_button(label="Select CAD File", callback=lambda: dpg.show_item("stl_select"), width=200)
            dpg.add_text("  Directory: ")
            dpg.add_text(stl_dir, tag="stl_text")
            
        # Select the Config File
        with dpg.group(horizontal=True):
            dpg.add_text("default:", tag="text_default_config")
            dpg.add_checkbox(label="    ", callback=default_config_path,  tag="checkbox_config")
            
            dpg.add_button(label="Select Prusaslicer Config", callback=lambda: dpg.show_item("slicer_config"), width=200)
            dpg.add_text("  Directory: ")
            dpg.add_text(config_dir, tag="config_text")
            
        with dpg.group(horizontal=True):
            dpg.add_button(label="Change Prusaslicer DIR", callback=lambda: dpg.show_item("slicer_select"), width=200)
            dpg.add_text(" Current Directory: ")
            dpg.add_text(prusaslicer_default_path, tag="slicer_text")
        
        with dpg.group(horizontal=True):
            dpg.add_text("")
            
        with dpg.group(horizontal=True):
            dpg.add_text("----------------------------------- Slicing options ----------------------------------------------")
        
        # Select the Case with checkboxes
        with dpg.group(horizontal=True):
            dpg.add_text("Select a Method:     ")
            dpg.add_text("Method 1 ", tag="text_case1")
            
            dpg.add_checkbox(label="     ", tag="checkbox_case1", callback=case1_marked, default_value=True)
            dpg.add_text("Method 2", tag="text_case2")
            dpg.add_checkbox(tag="checkbox_case2", callback=case2_marked)
            
            dpg.add_text('   Set numbers of planar baselayer', show=False, tag='text_planar_baselayer')
            dpg.add_input_int(tag = 'planar_baselayer', default_value=default_planar_baselayer, width=70, show=False)
            
        with dpg.group(horizontal=True):
            dpg.add_text("Select the maximal printing angle:", tag ='text_max_angle')
            dpg.add_input_int(tag = 'max_angle_input', default_value=max_angle_default, width=100)
            dpg.add_text("       select STL transform method:",tag="dropdown_text", show=False)
            dpg.add_listbox(tag = 'dropdown', items=["mirror", "interpolate"], callback=dropdown_callback, show = False, width=90)
            
        with dpg.group(horizontal=True):
            dpg.add_text("Add offset from outline", tag = "text_offset_value")
            dpg.add_checkbox(tag="checkbox_outline_offset", default_value=False, callback=outline_offset_marked, show=True)
            dpg.add_text("    ")
            dpg.add_input_float(label = "in mm", tag="outline_offset_value", default_value= outline_offset_default, show=False, width= 100)
            
        with dpg.group(horizontal=True):
            dpg.add_text("---------------------------------- Start Calculation ---------------------------------------------")
        
        # Select the Calculate Button
        with dpg.group(horizontal=True):   
            dpg.add_button(label="Calculate GCode", callback=calculate_button)
            dpg.add_button(label="Open Nonplanar GCode", callback=show_gcode_prusaslicer)
            
        with dpg.group(horizontal=True):        
            dpg.add_loading_indicator(tag="loading", show=False, radius=1.5)
            dpg.add_text("", tag="showtext_calculate_button")
                
            
    #Tooltips: (hovering over Items to show additional Information)
        # Case 1 Infos
        with dpg.tooltip("text_case1"):
                dpg.add_text("Method 1 scales a sliced and transformed .stl depending on the surface\n The Layerheight is calculated depending on the surface its mean height\nSurfacepoints above the mean get stretched and those below get compressed")
        
        # Case 2 Infos      
        with dpg.tooltip("text_case2"):
                dpg.add_text("Method 2 transforms the gcode of the mirrored .stl\n The Layerheight is constant but every layer is parallel to the surface\n The original .stl gets mirrored upside down and transformed, until the bottom is flat")
                
        with dpg.tooltip("slicer_text"):
                dpg.add_text("Add the Path to the folder where the prusa-slicer.exe is located.")
        
        with dpg.tooltip("text_offset_value"):
                dpg.add_text("The Offset is required when you have a radius on the outer edge of the part. \nChoose the offset according to the radius in mm")
        
        # Default Path for CAD Infos     
        with dpg.tooltip("text_default_cad"):
            dpg.add_text("The default Path is:")
            dpg.add_text(stl_default)
        
        # Default Path for Config file Infos    
        with dpg.tooltip("text_default_config"):
            dpg.add_text("The default Path is:")
            dpg.add_text(config_default)
            
        with dpg.tooltip('text_max_angle'):
            dpg.add_text("Angle between the horizontal plane and the surface")
            
    # Create the Window with custom Commands
    dpg.create_viewport(title='Nonplanar Slicing', width=1000, height=500)
        
    # Create the window and show it to the user
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()