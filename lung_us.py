# Script to create de-identified mp4
# To run this script, paste the following into the terminal: (MacOS)
# /Applications/Slicer.app/Contents/MacOS/Slicer --no-splash --no-main-window --python-script "/Users/fryderykkogl/Documents/university/master/thesis/code/mthesis-datasets/lung_us.py"
import os

import numpy as np
from pydicom import read_file
import sys
import logging.config

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


# this stays for debugging purposes if we want to load data here
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
    frame_size = np_array.shape[1:-1]

    # rgb to bgr
    buf = np_array.copy()
    np_array[:, :, :, 0] = buf[:, :, :, 2]
    np_array[:, :, :, 2] = buf[:, :, :, 0]

    # create video writer
    out = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*codec), fps, frame_size[::-1], isColor=True)

    # loop through all frames and write them to the video writer
    # dimensions have to be inverted for the VideoWriter
    for i in range(np_array.shape[0]):
        img = np_array[i, :, :, :].astype('uint8')
        out.write(img)

    # release the writer
    out.release()


def deidentify_us_images(np_array, crop_from_left=0.0, crop_from_top=0.0):
    """
    Function to de-identify (crop top x rows) US images
    :param np_array: input array of dim: AxBx[no. of frames]
    :param crop_from_top: how many rows from the top will be cropped
    :param crop_from_left: how many columns from the left will be cropped
    :return: the de-identified array
    """

    dims = np_array.shape

    left = int(np.ceil(dims[2] * crop_from_left))
    top = int(np.ceil(dims[1] * crop_from_top))

    # crop first <crop_from_top> rows
    cropped = np_array[:, top:, :-left, :]

    return cropped


def one_dicom(dicom_path, save_path):
    """
    Takes in one dicom path and saves it as an mp4 to the save path
    :param dicom_path:
    :param save_path:
    """
    # load us volume to slicer
    us_node = slicer.util.loadVolume(dicom_path)

    # get data array as numpy array
    us_numpy = slicer.util.arrayFromVolume(us_node)

    # us_numpy = load_dicom_to_numpy(dicom_path)

    # deidentify by cropping
    us_numpy = deidentify_us_images(us_numpy.copy(), crop_from_left=0.003125, crop_from_top=0.09166)

    # create video
    export_array_to_video(us_numpy, save_path=save_path)

    # remove node
    slicer.mrmlScene.RemoveNode(us_node)


# last folder for now: /Users/fryderykkogl/Dropbox (Partners HealthCare)/ED COVID Ultrasound Data/Case-211-46120713
# first folder: /Users/fryderykkogl/Dropbox (Partners HealthCare)/ED COVID Ultrasound Data/Case-176-03055225

"""
1. Go into each directory
    2. get all dicoms from folder starting with '2022'.../IMAGES
    3. create new directory DEIDENTIFIED CLIPS (next to '2022...'
    4. convert and save all dicoms to deidentified - name them 'US_BEDSIDE_1_2_crop' where '2' is a counter starting at one


    /Users/fryderykkogl/Dropbox (Partners HealthCare)/ED COVID Ultrasound Data/Case-179-32362410/2022-02-23-002/IMAGES/IM00018

"""

def main(params):

    folders = [
        # "/Users/fryderykkogl/Data/us_lung/Case-176-03055225",
        # "/Users/fryderykkogl/Data/us_lung/Case-179-32362410",
        # "/Users/fryderykkogl/Data/us_lung/Case-180-14455273",
        # "/Users/fryderykkogl/Data/us_lung/Case-181-09542382",
        # "/Users/fryderykkogl/Data/us_lung/Case-182-10071249",
        # "/Users/fryderykkogl/Data/us_lung/Case-183-24558363",
        # "/Users/fryderykkogl/Data/us_lung/Case-184-18207381",
        # "/Users/fryderykkogl/Data/us_lung/Case-185-46271896",
        # "/Users/fryderykkogl/Data/us_lung/Case-186-24605453",
        # "/Users/fryderykkogl/Data/us_lung/Case-187-05243787",
        # "/Users/fryderykkogl/Data/us_lung/Case-188-23406242",
        # "/Users/fryderykkogl/Data/us_lung/Case-189-11408499",
        # "/Users/fryderykkogl/Data/us_lung/Case-190-17497652",
        # "/Users/fryderykkogl/Data/us_lung/Case-191-26946673",
        # "/Users/fryderykkogl/Data/us_lung/Case-192-41155904",
        # "/Users/fryderykkogl/Data/us_lung/Case-193-46445441",
        # "/Users/fryderykkogl/Data/us_lung/Case-194-23898919",
        # "/Users/fryderykkogl/Data/us_lung/Case-195-46394383",
        # "/Users/fryderykkogl/Data/us_lung/Case-196-14485726",
        # "/Users/fryderykkogl/Data/us_lung/Case-197-16838849",
        "/Users/fryderykkogl/Data/us_lung/Case-198-46500187",
        "/Users/fryderykkogl/Data/us_lung/Case-199-27370832",
        "/Users/fryderykkogl/Data/us_lung/Case-200-7611373",
        "/Users/fryderykkogl/Data/us_lung/Case-201-05229976",
        "/Users/fryderykkogl/Data/us_lung/Case-202-18371294",
        "/Users/fryderykkogl/Data/us_lung/Case-203-41524711",
        "/Users/fryderykkogl/Data/us_lung/Case-204-42219576",
        "/Users/fryderykkogl/Data/us_lung/Case-205-01434364",
        "/Users/fryderykkogl/Data/us_lung/Case-206-41170069",
        "/Users/fryderykkogl/Data/us_lung/Case-207-08740458",
        "/Users/fryderykkogl/Data/us_lung/Case-208-19260322",
        "/Users/fryderykkogl/Data/us_lung/Case-209-11382090",
        "/Users/fryderykkogl/Data/us_lung/Case-210-23503139",
        "/Users/fryderykkogl/Data/us_lung/Case-211-46120713",
        "/Users/fryderykkogl/Data/us_lung/Case-212-11580156",
        "/Users/fryderykkogl/Data/us_lung/Case-213-27441609",
        "/Users/fryderykkogl/Data/us_lung/Case-214-01143797",
        "/Users/fryderykkogl/Data/us_lung/Case-215-46731071",
        "/Users/fryderykkogl/Data/us_lung/Case-216-15588197",
    ]

    try:

        logging.basicConfig(filename="/Users/fryderykkogl/Desktop/lung_log.log",
                            filemode='a',
                            format='%(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.DEBUG)
        logger = logging.getLogger()
        logger.debug("\n\n\n\n")

        # go into each directory
        for folder in folders:
            with open(f"/Users/fryderykkogl/Desktop/logs/{folder[-17:]}.txt", 'a+') as logger_file:
                logger_file.write("\n\n\n\n")
                logger.debug(f"\n{folder}")
                logger_file.write(f"\n\n{folder}\n")

                # get folder starting with date 2022
                subdirs = os.listdir(folder)
                dicom_parent_folder = None
                for subdir in subdirs:
                    if "2022" in subdir:
                        dicom_parent_folder = os.path.join(folder, subdir)
                        break

                # get dicom folder
                dicom_folder = os.path.join(dicom_parent_folder, "IMAGES")

                # loop through dicoms
                dicoms = []
                for idx, file in enumerate(os.listdir(dicom_folder)):
                    if "store" not in file.lower():
                        dicoms.append(os.path.join(dicom_folder, file))

                dicoms.sort()
                for idx, dicom in enumerate(dicoms):
                    load_path = os.path.join(dicom_folder, dicom)
                    save_path = os.path.join(folder, "DEIDENTIFIED CLIPS", f"US_BEDSIDE_1_{idx+1}_crop.mp4")

                    if not os.path.exists(os.path.join(folder, "DEIDENTIFIED CLIPS")):
                        os.makedirs(os.path.join(folder, "DEIDENTIFIED CLIPS"))

                    try:
                        one_dicom(load_path, save_path)
                    except:
                        pass

                    # if the created file does not exist, log it
                    if not os.path.exists(save_path):
                        logger.error(f"ERROR: {save_path}")
                        logger_file.write(f"ERROR: {save_path}\n")

                #logger_file.close()

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


def pixel_check(path_vid_ori, path_vid_new):
    """
    check if two videos are the same - pixelwise SSD. Returns the SSD of original with itself inversed and of original
    and the new
    :param path_vid_ori: Path to the original video
    :param path_vid_new: Path to the new video
    :return: (inverse_SSD, SSD)
    """
    def ssd(a, b):
        """
        Returns the Sum of Squared Differences of 'a' and 'b'
        :param a: Array 1
        :param b: Array 2
        :return: SSD
        """
        dif = a.flatten().astype('int64') - b.flatten().astype('int64')
        return np.dot(dif, dif)

    # load videos as numpy arrays
    cap = cv2.VideoCapture(path_vid_ori)
    ret = True
    ori_frames = []
    while ret:
        ret, img = cap.read()  # read one frame from the 'capture' object; img is (H, W, C)
        if ret:
            ori_frames.append(img)
    cap = cv2.VideoCapture(path_vid_new)
    ret = True
    new_frames = []
    while ret:
        ret, img = cap.read()  # read one frame from the 'capture' object; img is (H, W, C)
        if ret:
            new_frames.append(img)

    ori = np.array(ori_frames)
    ori_inv = 255 - ori
    new = np.array(new_frames)

    return ssd(ori, ori_inv), ssd(ori, new)


