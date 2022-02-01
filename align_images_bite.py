import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
import argparse
import utils

# script to align image and tumor from BITE (not register, just utilise the alignemnt which is stored int the files)

parser = argparse.ArgumentParser()
parser.add_argument("-sl", "--slice", type=int, default=20, help="Slice id (z-direction)")
parser.add_argument("-ty", "--type", type=str, default="tumor", choices=["combined", "tumor", "mri"], help="object "
                                                                                                              "to be "
                                                                                                              "displayed")
arguments = parser.parse_args()

tumor = nib.load("/mnt/c/Users/fryde/Documents/University a/Master/Master\'s "
                 "thesis/Datasets/BITE/group3/01/01_tumor.mnc")
preop = nib.load("/mnt/c/Users/fryde/Documents/University a/Master/Master\'s "
                 "thesis/Datasets/BITE/group3/01/01_preop_mri.mnc")

tumor_03_01_01_start = np.asarray([-12.1112, 53.5189, -18.3051])
preop_03_01_01_start = np.asarray([-84.2999, -81.3051, -145.008])
diff = np.floor(tumor_03_01_01_start - preop_03_01_01_start).astype(int)

tumor_data = tumor.get_fdata()
mri_data = preop.get_fdata()

t_shape = tumor_data.shape
buffer = np.zeros(mri_data.shape)

buffer[diff[0]:diff[0] + t_shape[0], diff[1]:diff[1] + t_shape[1], diff[2]:diff[2] + t_shape[2]] = tumor_data
tumor_new = buffer

slice_id = arguments.slice
slice_tumor = tumor_new[slice_id, :, :]
slice_mri = mri_data[slice_id, :, :] / 255

combined = slice_mri + slice_tumor

#fig = plt.figure(1)
#plt.imshow(slice_tumor)
#plt.show()

fig2 = plt.figure()

if arguments.type == "combined":
    plt.imshow(combined)
elif arguments.type == "tumor":
    plt.imshow(slice_tumor)
elif arguments.type == "mri":
    plt.imshow(slice_mri)

plt.show()
