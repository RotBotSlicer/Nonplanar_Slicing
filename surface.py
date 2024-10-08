# This file creates a Mesh for the top Surface of the stl File
from scipy.interpolate import griddata
import numpy as np
import scipy.ndimage
from scipy.spatial import distance
from shapely.geometry import Polygon, Point


## Input:   stl_triangles   = Numpy array of shape [NUMBER_TRIANGLES,12] with [_,:] = [x_normal,y_normal,z_normal,x1,y1,z1,x2,y2,z2,x3,y3,z3]

## Use:     

## Output:  

def detectSortOutline(stl_triangles: 'np.ndarray[np.float]'):
    #stl_triangles[:,[5,8,11]] = 0
    testarr = ~np.bitwise_and.reduce((np.isclose(stl_triangles[:,5::3],np.zeros_like(stl_triangles[:,5::3]),atol=0.01)),axis=1) #detects lines where z is sufficiently close to 0
    base_triangles = np.delete(stl_triangles,testarr,axis=0) #gets rid of all lines where z is not within a specified tolerance to 0

    triangles_check = np.concatenate((base_triangles[:,[3,4,6,7]],base_triangles[:,[6,7,9,10]],base_triangles[:,[3,4,9,10]]),axis=0)
    triangles_check = np.concatenate((triangles_check,triangles_check[:, [2, 3, 0, 1]]))

    uniq,idx,count= np.unique(triangles_check,return_index=True,return_counts=True,axis=0)
    count = count[idx.argsort()]
    uniq = uniq[idx.argsort()]
    uniq = uniq[np.logical_not((count-1).astype(bool))]
    uniq = uniq[:len(uniq)//2]
    outline = np.empty((len(uniq[:,0])+1,2))
    outline[0] = uniq[0,0:2]
    for i, point in enumerate(outline):   #check where the points occur again
        idr1 =  np.where(np.all(uniq[:,:2] == point,axis=1))[0]
        idr2 =  np.where(np.all(uniq[:,2:] == point,axis=1))[0]
        if idr1.size != 0:
            outline[i+1] = uniq[idr1[0],2:]
            uniq[idr1[0],:] = np.nan
        elif idr2.size != 0:
            outline[i+1] = uniq[idr2[0],:2]
            uniq[idr2[0],:] = np.nan
    return outline


## Input:   Numpy array of shape [NUMBER_TRIANGLES,12] with [_,:] = [x_normal,y_normal,z_normal,x1,y1,z1,x2,y2,z2,x3,y3,z3]
           # maximum of the possible angle for the surface, here between the surface and the horizontal plane

## Use:     Calculates the angle between every normalvector and the horizontal plane

## Output:  surface_filtered = 3 Columnvectors: 2 coordinates with the corresponding z value
#           limits = np.array with the values [xmin, xmax, ymin, ymax]

def create_surface(stl_triangles, max_angle):
    
    limits = np.zeros((4))
    limits[0] = np.amin([stl_triangles[:,3],stl_triangles[:,6], stl_triangles[:,9]])
    limits[1] = np.amax([stl_triangles[:,3],stl_triangles[:,6], stl_triangles[:,9]])
    limits[2] = np.amin([stl_triangles[:,4],stl_triangles[:,7], stl_triangles[:,10]])
    limits[3] = np.amax([stl_triangles[:,4],stl_triangles[:,7], stl_triangles[:,10]])
    
    for i in range(0,4):
        limits[i] = np.sign(limits[i]) * np.ceil(np.abs(limits[i]) + 0.5)
    
    
    u = stl_triangles[:,0:3]                        # Create an Array with the normalvector values

    c = u[:,2] / np.linalg.norm(u, axis=1)          # -> cosine of the angle
    calc_angle = np.arccos(np.clip(c, -1, 1))       # Calculate the angle between the 2 vectors

    filtered_array = np.delete(stl_triangles[:,3:], np.where(calc_angle > max_angle)[0], axis=0) # deletes all Indexes in the main Array where the angles > max_angle
    surface_points = np.concatenate([filtered_array[:, 0:3], filtered_array[:, 3:6], filtered_array[:, 6:9]], axis=0) # convert all points into 1 array
    surface_filtered = np.unique(surface_points, axis=0) # Delete every duplicate point in the array
    
    ##  surface_filtered contains x,y,z points of the surface
    #   surface_filtered[x, y, z]
    
    return surface_filtered, limits


## Input:   Numpy array of shape [NUMBER_TRIANGLES,12] with [_,:] = [x_normal,y_normal,z_normal,x1,y1,z1,x2,y2,z2,x3,y3,z3]
           # maximum of the possible angle for the surface, here between the surface and the horizontal plane

## Use:     Calculates the angle between every normalvector and the horizontal plane and extrapolates the nearest point of the surface (extrapolate) and gauss filter the surface

## Output:  gives back 3 Columnvectors: 2 coordinates with the corresponding z value

def create_surface_extended(surface_filtered, limits, resolution):
    
    
    Xmesh, Ymesh = np.meshgrid(np.arange(round(limits[0], 1), round(limits[1], 1), resolution), np.arange(round(limits[2], 1), round(limits[3], 1), resolution))

    Zmesh = griddata((surface_filtered[:,0], surface_filtered[:,1]), surface_filtered[:,2], (Xmesh, Ymesh), method='cubic',rescale=True)

    #Zmesh[np.isnan(Zmesh)] = 0
    Zmesh_ext = griddata((surface_filtered[:,0], surface_filtered[:,1]), surface_filtered[:,2], (Xmesh, Ymesh), method='nearest')
    #index = np.isclose(Zmesh, 0, 1e-15)
    index = np.isnan(Zmesh)
    Zresult = Zmesh.copy()

    Zmesh_ext = scipy.ndimage.gaussian_filter(Zmesh_ext, sigma=5)

    Zresult[index] = Zmesh_ext[index]
    
    #Zresult = scipy.ndimage.gaussian_filter(Zresult, sigma=2)
    
    
    return Xmesh, Ymesh, Zresult

# Same as "create_surface_extended" but specific for case / method 1

def create_surface_extended_case1(surface_filtered, limits, resolution):
    
    
    Xmesh, Ymesh = np.meshgrid(np.arange(round(limits[0], 1), round(limits[1], 1), resolution), np.arange(round(limits[2], 1), round(limits[3], 1), resolution))

    Zmesh = griddata((surface_filtered[:,0], surface_filtered[:,1]), surface_filtered[:,2], (Xmesh, Ymesh), method='cubic')
    Zmesh[np.isnan(Zmesh)] = 0
    Zmesh_ext = griddata((surface_filtered[:,0], surface_filtered[:,1]), surface_filtered[:,2], (Xmesh, Ymesh), method='nearest')
    index = np.isclose(Zmesh, 0, 1e-15)
    Zresult = Zmesh.copy()
    Zresult[index] = Zmesh_ext[index]
    
    Zresult = scipy.ndimage.gaussian_filter(Zresult, sigma=7)
    
    
    return Xmesh, Ymesh, Zresult


## Input:  points_to_interpolate       -> give the wanted interpolated Points in an [n,2] numpy Array
#          reference_points            -> the given datapoints of the Surface [n, (x,y,z)]
#          Method to interpolate       -> {"linear", "nearest", "cubic"}

## Use:    Interpolation of the given Points of the Surface with finite Points

## Output: 1 Numpy Array with the interpolated z values and the Shape [n,1] 

def interpolate_grid(points_to_interpolate, reference_points, method_interpol = 'linear'):
       
    # Create the interpolated grid
    z_interpol = griddata(reference_points[:,:2], reference_points[:,2], (points_to_interpolate[:,0], points_to_interpolate[:,1]), method_interpol)
    return z_interpol


## Input:   surface_data                -> the given surface points with shape = [n,3] and the 3 column are (x,y,z)

## Use:     once calculation of the gradient for extrusion compensation

## Output:  gradient mesh from the surface
    
    
def create_gradient(surface_data, limits=0):
   
    if str(limits) != '0':
        x_min = limits[0]
        x_max = limits[1]
        y_min = limits[2]
        y_max = limits[3]
    else:
        x_min = np.min(surface_data[:,0])
        x_max = np.max(surface_data[:,0])
        y_min = np.min(surface_data[:,1])
        y_max = np.max(surface_data[:,1])
        
   
    Xmesh, Ymesh = np.meshgrid(np.arange(np.round(x_min, 1), np.round(x_max, 1), 0.5), np.arange(np.round(y_min, 1), np.round(y_max, 1), 0.5))

    # Verwende griddata fuer die Interpolation
    Zmesh = griddata((surface_data[:,0], surface_data[:,1]), surface_data[:,2], (Xmesh, Ymesh), method='cubic')

    # Berechne die Gradienten
    GradX, GradY = np.gradient(Zmesh)
    GradZ = np.sqrt(GradX**2 + GradY**2)
    GradZ[np.isnan(GradZ)] = 0
    return Xmesh, Ymesh, GradZ

## Input:  Numpy array of shape [NUMBER_TRIANGLES,12] with [_,:] = [x_normal,y_normal,z_normal,x1,y1,z1,x2,y2,z2,x3,y3,z3] 

## Use:    Calculates the 2d outline from an object

## Output:  Points of the Outline only -> points inside are not included
#           2 Vectors with the Shape [n,1] for the x and y Values of the Outline



## Input:   surface_data            -> the given datapoints of the Surface [n, (x,y,z)]
#           resolution              -> in mm how big the steps for the surface reference array should be

## Use:     Creates an Array in (resolution) mm steps to reduce the time calculating the interpolation for the surface

## Output:  gives the interpolated Zmesh for the corresponding points in the array

def create_surface_array(surface_data, resolution, limits=0):
 
    if str(limits) != '0':
        x_min = limits[0]
        x_max = limits[1]
        y_min = limits[2]
        y_max = limits[3]
    else:
        x_min = np.min(surface_data[:,0])
        x_max = np.max(surface_data[:,0])
        y_min = np.min(surface_data[:,1])
        y_max = np.max(surface_data[:,1])
   
    Xmesh, Ymesh = np.meshgrid(np.arange(round(x_min, 1), round(x_max, 1), resolution), np.arange(round(y_min, 1), round(y_max, 1), resolution))

    # Verwende griddata f�r die Interpolation
    Zmesh = griddata((surface_data[:,0], surface_data[:,1]), surface_data[:,2], (Xmesh, Ymesh), method='cubic')
    
    return Zmesh

## Input:   Triangle_array = STL Triangles in shape [NUMBER_TRIANGLES,12] with [_,:] = [x_normal,y_normal,z_normal,x1,y1,z1,x2,y2,z2,x3,y3,z3] 

## Use:     Extracts the contour of the lowest layer (Baseplate layer) and sort the contour according to their euclidian distance

## Output:  Array of sorted points
 
def sort_contour(triangle_array):
    
    testarr = ~np.bitwise_and.reduce((np.isclose(triangle_array[:,5::3],np.zeros_like(triangle_array[:,5::3]),1e-17)),axis=1) #detects lines where z is sufficiently close to 0
    base_triangles = np.delete(triangle_array,testarr,axis=0) #gets rid of all lines where z is not within a specified tolerance to 0

    top_triangles = base_triangles.copy()
    top_triangles[:,2] *= -1
    base_triangles[:,[5,8,11]] = 0

    triangles_check = np.concatenate((base_triangles[:,[3,4,6,7]],base_triangles[:,[6,7,9,10]],base_triangles[:,[3,4,9,10]]),axis=0)
    triangles_check = np.concatenate((triangles_check,triangles_check[:, [2, 3, 0, 1]]))

    uniq,idx,count= np.unique(triangles_check,return_index=True,return_counts=True,axis=0)
    count = count[idx.argsort()]
    uniq = uniq[idx.argsort()]
    uniq = uniq[np.logical_not((count-1).astype(bool))]
    uniq = uniq[:len(uniq)//2]
    contour_unsorted = np.concatenate((uniq[:, [0,1]], uniq[:,[2,3]]), axis=0)
        
    points = np.column_stack((contour_unsorted[:,0], contour_unsorted[:,1]))
    dist_matrix = distance.cdist(points, points, 'euclidean')
    
    start_index = np.argmin(np.sum(dist_matrix, axis=1))
    
    sorted_indices = [start_index]
    unsorted_indices = set(range(len(points)))
    unsorted_indices.remove(start_index)
    
    while unsorted_indices:
        current_index = sorted_indices[-1]
        nearest_index = min(unsorted_indices, key=lambda i: dist_matrix[current_index, i])
        sorted_indices.append(nearest_index)
        unsorted_indices.remove(nearest_index)
    
    sorted_points = points[sorted_indices]
    
    return sorted_points

## Input:   outline_x = Outline of the sorted baselayer (only x coordinates)
#           outline_y = Outline of the sorted baselayer (only y coordinates)
#           surface   = Surface Array from create_surface() function
#           offset_distance = Offset from the outline

## Use:     Creates an Offset inwards from the sorted outline (from the baselayer) and deletes all points from the surface outside that area

## Output:  Surface points withing the defined section (offset distance from the outline)

def offset_contour(outline_x, outline_y, surface, offset_distance):

    polygon_points = np.column_stack((outline_x.flatten(), outline_y.flatten()))
    original_polygon = Polygon(polygon_points)

    offset_polygon = original_polygon.buffer(-offset_distance)

    points_to_compare = surface[:,:2]
    points_inside_offset = [Point(point).within(offset_polygon) for point in points_to_compare]

    filtered_points = surface[points_inside_offset]

    reduced_contour_points = np.column_stack(offset_polygon.exterior.xy)
    z_values_contour = griddata((surface[:,0], surface[:,1]), surface[:,2], (reduced_contour_points[:,0], reduced_contour_points[:,1]), 'cubic')
    reduced_contour = np.zeros([reduced_contour_points.shape[0], 3])
    reduced_contour[:,:2] = reduced_contour_points
    reduced_contour[:,2] = z_values_contour
    filtered_points = np.concatenate((filtered_points, reduced_contour), axis=0)

    return filtered_points


## Input:   Numpy array  = [x_normal,y_normal,z_normal,x1,y1,z1,x2,y2,z2,x3,y3,z3] 

## Use:     Splits a single triangle into 4 smaller triangles

## Output:  4 triangles
def split_triangle_4(triangle: 'np.ndarray'):
    points = triangle.reshape(-1,3)
    ip1 = points[2] + (points[1]-points[2])/2
    ip2 = points[3] + (points[2]-points[3])/2
    ip3 = points[1] + (points[3]-points[1])/2
    triangles = np.concatenate((np.concatenate((points[0],ip1,ip2,ip3)),
                                np.concatenate((points[0],points[1],ip1,ip3)),
                                np.concatenate((points[0],points[2],ip1,ip2)),
                                np.concatenate((points[0],points[3],ip2,ip3))
                                ))
    triangles=triangles.reshape(-1,12)
    return triangles

## Input:   stl_data    = STL Triangles in shape [NUMBER_TRIANGLES,12] with [_,:] = [x_normal,y_normal,z_normal,x1,y1,z1,x2,y2,z2,x3,y3,z3]
#           iterations  = number of dividing every triangle in 4 smaller

## Use:     Scales the resolution up from an STL

## Output:  upscaled STL with the Shape [NUMBER_UPSCALED_TRIANGLES,12] with [_,:] = [x_normal,y_normal,z_normal,x1,y1,z1,x2,y2,z2,x3,y3,z3]
def upscale_stl(stl_data: 'np.ndarray', iterations = 1):
    stl_upscaled = stl_data
    for j in range(iterations):
        print(f'Upscaling -> {(100/iterations)*j:.{1}f}%')
        stl_upscaled = np.empty((4*len(stl_data[:,0]),12))
        for i,triangle in enumerate(stl_data):
            stl_upscaled[i*4:(i*4)+4] = split_triangle_4(triangle)
        stl_data = stl_upscaled
    print('Upscaling -> 100.0%')
    return stl_upscaled



