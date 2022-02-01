from pyminc.volumes.factory import *
import matplotlib.pyplot as plt
import numpy as np
import sys


def main():

    tumor_path = "/mnt/c/Users/fryde/Documents/University a/Master/Master\'s " \
                 "thesis/Datasets/BITE/group3/01/01_tumor.mnc"
    preop_path = "/mnt/c/Users/fryde/Documents/University a/Master/Master\'s " \
                 "thesis/Datasets/BITE/group3/01/01_preop_mri.mnc"

    # get the input file
    preop = volumeFromFile(preop_path)
    data_mri = preop.data

    slice_id = 50

    slice_mri = data_mri[slice_id, :, :] / 255

    save_data = np.asarray(slice_mri)

    with open('test.npy', 'wb') as f:
        np.save(f, save_data)

    # get the output file using the same dimension info as the input file
    # outfile = volumeLikeFile(preop_path, preop_path)

    # add one to the data
    # outfile.data = infile.data + 1

    # write out and close the volumes
    # outfile.writeFile()
    # outfile.closeVolume()
    # infile.closeVolume()


if __name__ == "__main__":
    main()
