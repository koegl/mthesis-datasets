import numpy as np
import argparse
import os
import nibabel as nib
import utils


def main(args):

    file_path = args.file_path
    directory = args.directory
    tag = args.search_tag

    tumor_paths = []

    if directory is not None and tag is not None:
        tumor_paths = [os.path.join(path, name) for path, subdirs, files in os.walk(directory) for name in files
                       if tag in name]

    if file_path is not None:
        tumor_paths = [file_path]

    for tumor in tumor_paths:

        nifti = nib.load(tumor)
        utils.volumetric_plot(nifti, volume_type="tumor")


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--directory", type=str, default=None, help="Directory in which mnc files will be"
                                                                          "searched for and converted to nii")
    parser.add_argument("-fp", "--file_path", type=str, default=None, help="File path of the file to be displayed")
    parser.add_argument("-st", "--search_tag", type=str, default="tumor.nii", help="String that has to be included in"
                                                                                   "the filename")

    arguments = parser.parse_args()

    main(arguments)
