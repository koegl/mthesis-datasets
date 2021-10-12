import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt

tumor = nib.load("/mnt/c/Users/fryde/Documents/University a/Master/Master\'s "
                 "thesis/Datasets/BITE/group3/01/01_tumor.nii")
preop = nib.load("/mnt/c/Users/fryde/Documents/University a/Master/Master\'s "
                 "thesis/Datasets/BITE/group3/01/01_preop_mri.nii")

tumor_03_01_01_start = np.asarray([-12.1112, 53.5189, -18.3051])
preop_03_01_01_start = np.asarray([-81.3051, -84.2999, -145.008])
diff = np.floor(tumor_03_01_01_start - preop_03_01_01_start).astype(int)

tumor_data = tumor.get_fdata()
mri_data = preop.get_fdata()

t_shape = tumor_data.shape
buffer = np.zeros(mri_data.shape)

buffer[diff[0]:diff[0] + t_shape[0], diff[1]:diff[1] + t_shape[1], diff[2]:diff[2] + t_shape[2]] = tumor_data
tumor_new = buffer

slice_id = 129
slice_tumor = tumor_new[:, :, slice_id]
slice_mri = mri_data[:, :, slice_id] / 255

combined = slice_mri + slice_tumor

#fig = plt.figure(1)
#plt.imshow(slice_tumor)
#plt.show()

fig2 = plt.figure()
plt.imshow(combined)
plt.show()

input()
