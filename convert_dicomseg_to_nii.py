# script to convert dicom segmentations from brainlab to niftii when SLicer cannot load them (even afte decompression)

import sys
import numpy as np
import SimpleITK as sitk
import os
import nibabel as nib


def main():
    # get all files
    file_path = sys.argv[1]

    # create temp folder in parent folder of file_path
    temp_folder = os.path.dirname(file_path) + "/temp"
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    # copy file from file_path to temp folder
    temp_file = temp_folder + "/" + os.path.basename(file_path)
    os.system("cp " + "\"" + file_path + "\"" + " " + "\"" + temp_folder + "\"")

    # extarct dicom data
    series_i_ds = sitk.ImageSeriesReader.GetGDCMSeriesIDs(temp_folder)
    series_file_names = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(temp_folder, series_i_ds[0])
    series_reader = sitk.ImageSeriesReader()
    series_reader.SetFileNames(series_file_names)
    series_reader.LoadPrivateTagsOn()
    segmentation = series_reader.Execute()

    spacing = segmentation.GetSpacing()
    origin = np.asarray(segmentation.GetOrigin())
    origin[0] *= -1
    origin[1] *= -1
    direction = np.asarray(segmentation.GetDirection())
    direction = np.reshape(direction, (4, 4))
    direction[0:3, -1] = origin[:-1]
    direction[0][0] *= -1
    # direction[1][1] *= -1

    for i in range(3):
        direction[i][i] *= spacing[i]

    # save nifti
    nii_file = nib.Nifti1Image(np.squeeze(sitk.GetArrayFromImage(segmentation)), direction)
    nib.save(nii_file, file_path)

    # remove temp file and temp folder
    os.system("rm " + "\"" + temp_file + "\"")
    os.system("rm -r " + "\"" + temp_folder + "\"")


if __name__ == "__main__":
    main()


