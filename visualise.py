import numpy as np
import argparse
import os
import nibabel as nib
import utils


def main(args):

    file_path = args.file_path
    directory = args.directory

    tumor_paths = [os.path.join(path, name) for path, subdirs, files in os.walk(directory) for name in files
                   if "tumor.nii" in name]

    for tumor in tumor_paths:

        nifti = nib.load(tumor)
        utils.volumetric_plot(nifti, volume_type="tumor")


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--directory", type=str, default=None, help="Directory in which mnc files will be"
                                                                          "searched for and converted to nii")
    parser.add_argument("-fp", "--file_path", type=str, default=None, help="File path of the file to be displayed")

    arguments = parser.parse_args()

    main(arguments)
