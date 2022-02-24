# Script to create de-identified mp4
# To run this script, paste the following into the terminal: (MacOS)
# /Applications/Slicer.app/Contents/MacOS/Slicer --no-splash --no-main-window --python-script "/Users/fryderykkogl/Documents/university/master/thesis/code/mthesis-datasets/lung_us.py"

import numpy as np
from pydicom import read_file
import sys

try:
    import cv2
except:
    slicer.util.pip_install('opencv-python')
    import cv2
try:
    import matplotlib.pyplot as plt
except:
    slicer.util.pip_install('matplotlib')
    import matplotlib.pyplot as plt

import slicer


def plot(array):
    plt.imshow(array, cmap='gray')
    plt.show()


def export_array_to_video(np_array, save_path='/Users/fryderykkogl/Desktop/output_video.mp4', codec='H264', fps=26.09):
    """
    Exports numpy array to video
    :param np_array: input array of dim: AxBx[no. of frames]
    :param save_path: Path where the video will be saved (extension included in path)
    :param codec: fourcc codec
    :param fps: Frames per second
    """
    # get images shape
    frame_size = np_array.shape[1:]
    buf = np_array.copy()
    np_array[:, :, :, 0] = buf[:, :, :, 2]
    np_array[:, :, :, 2] = buf[:, :, :, 0]

    # create video writer
    out = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*codec), fps, frame_size, isColor=False)

    # loop through all frames and write them to the video writer
    # dimensions have to be inverted for the VideoWriter
    for i in range(np_array.shape[0]):
        img = np.transpose(np_array[i, :, :].astype('uint8'))
        out.write(img)

    # release the writer
    out.release()


def deidentify_us_images(np_array, crop_from_left=0, crop_from_top=0):
    """
    Function to de-identify (crop top x rows) US images
    :param np_array: input array of dim: AxBx[no. of frames]
    :param crop_from_top: how many rows from the top will be cropped
    :param crop_from_left: how many columns from the left will be cropped
    :return: the de-identified array
    """

    # crop first <crop_from_top> rows
    cropped = np_array[:, crop_from_top:, crop_from_left:]

    return cropped


def load_dicom_to_numpy(dicom_path='CT_small.dcm'):
    """
    Function to load DICOMs and return the data as a numpy array of shape AxBx[no. of frames]
    :param dicom_path: Path to the DICOM
    :return: The numpy array with the data from DICOM
    """

    # read dicom
    ds = read_file(dicom_path)

    # return only the pixel values as a numpy array
    return ds.pixel_array


def main(params):

    try:
        # load us volume to slicer
        us_node = slicer.util.loadVolume("/Users/fryderykkogl/Documents/university/master/thesis/data.nosync/lung_us"
                                         "/IM00001")

        us_numpy = slicer.util.arrayFromVolume(us_node)

        # only use first channel
        us_numpy = us_numpy[:, :, :, 0]  # + us_numpy[:, :, :, 1] + us_numpy[:, :, :, 2]

        us_numpy = deidentify_us_images(us_numpy.copy(), crop_from_left=0, crop_from_top=42)

        us_numpy = downscale_numpy_to(us_numpy, (us_numpy.shape[0], 638, 436))
        # the numbers are extracted from original file

        export_array_to_video(us_numpy, save_path='/Users/fryderykkogl/Documents/university/master/thesis'
                                                  '/data.nosync/lung_us/my/output_video_ori.mp4')

        sys.exit(0)

    except Exception as e:
        print(f"could not export video.\n{e}")
        sys.exit(0)


if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    #
    # parser.add_argument("-mrb", "--mrb_path", type=str, help="Path to the the mrb to load",
    #                     default='/Users/fryderykkogl/Dropbox (Partners HealthCare)/Neurosurgery MR-US Registration Data'
    #                             '/Case AG2152/Harneet/AG2152-H editedL10.mrb')
    # parser.add_argument("-mln", "--markups_list_name", type=str, help="Name of the markups list",
    #                     default="AG2152")
    # parser.add_argument("-ep", "--export_path", type=str, help="Path to the pickle export",
    #                     default="/Users/fryderykkogl/Desktop/AG2152")
    #
    # arguments = parser.parse_args()

    main(None)  # arguments)
