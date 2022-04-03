# from deidentify_dcm.export_logic import ExportHandling
#
# import matplotlib.pyplot as plt
#
# def plot(array, cmap=None):
#     """
#     Plots a numpy array
#     :param array: The array to be displayed
#     :param cmap: The cmap for the plot
#     """
#     plt.imshow(array, cmap=cmap)
#     plt.show()
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
faulty_dicom = "/Users/fryderykkogl/Data/deidentify/retrospective_cases/Case-224-005725_problem/IMAGES/IM00001.dcm"
#
# export_handler.run_export_loop(path_list, crop_values)
#
# ds_normal = read_file(normal_dicom)
# pixels_normal = ds_normal.pixel_array
#
# ds_faulty = read_file(normal_dicom)
# pixels_faulty = ds_normal.pixel_array
#
# print(5)

import nibabel as nib
import nibabel.nicom.dicomwrappers


x = nib.load(faulty_dicom)