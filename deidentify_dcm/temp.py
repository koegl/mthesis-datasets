# from deidentify_dcm.export_logic import ExportHandling

import matplotlib.pyplot as plt
import numpy as np

def plot(array, cmap=None):
    """
    Plots a numpy array
    :param array: The array to be displayed
    :param cmap: The cmap for the plot
    """
    plt.figure()
    plt.imshow(array, cmap=cmap)
    plt.show()
#
# from pydicom.pixel_data_handlers.util import _convert_YBR_FULL_to_RGB
# from pydicom import read_file
#
# export_handler = ExportHandling()
#
# path_list = ["/Users/fryderykkogl/Data/deidentify/retrospective_cases/Case-224-005725_problem/IMAGES/IM00001"]
# crop_values = [0.09166, 0.0, 0.0, 0.0]
#
# normal_dicom = "/Users/fryderykkogl/Dropbox (Partners HealthCare)/MLSC Data/MLSC Data with PHI for BWH only/Lung/Case-286-2241482/IMAGES/IM00001"
faulty_dicom = "/Users/fryderykkogl/Dropbox (Partners HealthCare)/MLSC Data/MLSC Data with PHI for BWH only/Lung/Case-376-149483 (PHILIPS)_problem/IMAGES/IM00001"
#
# export_handler.run_export_loop(path_list, crop_values)
#
# ds_normal = read_file(normal_dicom)
# pixels_normal = ds_normal.pixel_array

from pydicom.pixel_data_handlers.util import apply_color_lut
from pydicom import read_file

ds_faulty = read_file(faulty_dicom)
pixels_faulty = ds_faulty.pixel_array
pixels_faulty = pixels_faulty.astype("float64")
pixels_faulty /= np.max(pixels_faulty)

x = apply_color_lut(pixels_faulty, ds_faulty)
x = x.astype('float64')
x /= np.max(x)

print(5)
