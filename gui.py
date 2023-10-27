import dearpygui.dearpygui as dpg
import dearpygui.demo as demo
import filereader as fr
import prusa_slicer as ps
import surface as sf
import numpy as np
import gcode_transform_1 as gc1
import os
import transform as tf

demo_on = 0

# Setup Default Paths if nothing is marked
stl_default = "Welle.stl"
config_default = "test_files/generic_config_Deltiq2.ini"

# Create the window with its Context
dpg.create_context()

# Standard comment as path
stl_dir = "C:/ "
config_dir = "C:/ "


# Interupthandling if a button or similiar is activated
def stl_chosen(sender, app_data, user_data):
    stl_dir = app_data["file_path_name"]
    dpg.set_value("checkbox_cad", False)
    dpg.set_value("stl_text", stl_dir)
    
def config_chosen(sender, app_data, user_data):
    config_dir = app_data["file_path_name"]
    dpg.set_value("checkbox_config", False)
    dpg.set_value("config_text", config_dir)
    
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
    else:
        dpg.set_value("checkbox_case1", True)
    
def case2_marked(sender, app_data, user_data):
    if app_data:
        dpg.set_value("checkbox_case1", False)
    else:
        dpg.set_value("checkbox_case2", True)
               
def calculate_button(sender, app_data, user_data):
    # if the paths are changed to a custom one
    if (len(dpg.get_value("stl_text")) > 4) and( len(dpg.get_value("config_text")) > 4):
        dpg.set_value("showtext_calculate_button", "calculation started")
    
    # else the Paths are changed to the default path
    else:
        dpg.set_value("showtext_calculate_button", "Info: Calculation started with default Path")
        
        stl_dir = stl_default
        dpg.set_value("stl_text", stl_dir)
        dpg.set_value("checkbox_cad", True)
        config_dir = config_default
        dpg.set_value("config_text", config_dir)
        dpg.set_value("checkbox_config", True)
    
    # Start with the calculation
    dpg.show_item("loading")
    orig_stl = fr.openSTL(dpg.get_value("stl_text"))
    filtered_surface = sf.create_surface(orig_stl,np.deg2rad(45))
    z_mean = np.average(filtered_surface[:,2])
    
# -----------------------Function for slicing etc. here -----------------------
    if dpg.get_value("checkbox_case1"):
        # Here goes the calculations for Case 1
        temp_stl_path = fr.writeSTL(fr.genBlock(orig_stl,z_mean))
        ps.sliceSTL(temp_stl_path,dpg.get_value("config_text"),'--info')
        orig_gcode = fr.openGCODE("output.gcode")
        gc1.trans_gcode(orig_gcode, filtered_surface)
        os.remove(temp_stl_path)
    
    if dpg.get_value("checkbox_case2"):
        # Here goes the calculations for Case 2
        transformed_stl = tf.projectSTL(orig_stl,filtered_surface,method='mirror')
        temp_stl_path = fr.writeSTL(transformed_stl)
        ps.sliceSTL(temp_stl_path,config_dir,'--info')
        ps.repairSTL(temp_stl_path)
        os.remove(temp_stl_path)
        planar_gcode = fr.openGCODE('output.gcode')

    # finishing informations for the User
    dpg.hide_item("loading")
    dpg.set_value("showtext_calculate_button", "Finished Gcode ready, Enjoy")
    

# Here are the File dialog defined
with dpg.file_dialog(directory_selector=False, show=False, callback=stl_chosen, id="stl_select", width=700 ,height=400):
    dpg.add_file_extension(".stl", color=(255, 255, 255, 255))

with dpg.file_dialog(directory_selector=False, show=False, callback=config_chosen, id="slicer_config", width=700 ,height=400):
    dpg.add_file_extension(".ini", color=(255, 255, 255, 255))

# Custom Window with the corresponding buttons etc.
with dpg.window(label="Slicer Settings", width=1000, height=500):
    
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
    
    # Select the Case with checkboxes
    with dpg.group(horizontal=True):
        dpg.add_text("Select a Case:     ")
        dpg.add_text("Case 1 ", tag="text_case1")
        
        dpg.add_checkbox(label="     ", tag="checkbox_case1", callback=case1_marked, default_value=True)
        dpg.add_text("Case 2", tag="text_case2")
        dpg.add_checkbox(tag="checkbox_case2", callback=case2_marked)
    
    # Select the Calculate Button
    with dpg.group(horizontal=True):   
        dpg.add_button(label="Calculate GCode", callback=calculate_button )
        dpg.add_loading_indicator(tag="loading", show=False, radius=1.5)
        dpg.add_text("", tag="showtext_calculate_button")
       
        
#Tooltips: (hovering over Items to show additional Information)
    # Case 1 Infos
    with dpg.tooltip("text_case1"):
            dpg.add_text("tbd: Hier kommt die Beschreibung von Fall 1 hinein")
    
    # Case 2 Infos      
    with dpg.tooltip("text_case2"):
            dpg.add_text("tbd: Hier kommt die Beschreibung von Fall 2 hinein")
       
    # Default Path for CAD Infos     
    with dpg.tooltip("text_default_cad"):
        dpg.add_text("The default Path is:")
        dpg.add_text(stl_default)
    
    # Default Path for Config file Infos    
    with dpg.tooltip("text_default_config"):
        dpg.add_text("The default Path is:")
        dpg.add_text(config_default)
        
# Create the Window with custom Commands
dpg.create_viewport(title='Nonplanar Slicing', width=1000, height=500)

#--------------------------------
# Delete late this rows...
# show the demo -> What is possible
if demo_on == 1:
    demo.show_demo()
#--------------------------------   
    
# Create the window and show it to the user
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
