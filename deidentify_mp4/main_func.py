import logging
import numpy as np
import cv2
from pathlib import Path
import argparse
import os
# -lp "/Users/fryderykkogl/Documents/university/master/thesis/data.nosync/IM00001.mov"

def load_video_to_numpy(video_path="/Users/fryderykkogl/Documents/university/master/thesis/data.nosync/nick/test/IM00001.mov"):
    """
    Function to load a video and return the data as a numpy array
    :param video_path: Path to the .mov
    :return: The numpy array with the data from the video [frames x [dim1, dim2] x 3]
    """

    # read video
    cap = cv2.VideoCapture(video_path)
    ret = True
    frames = []
    while ret:
        ret, img = cap.read()  # read one frame from the 'capture' object; img is (H, W, C)
        if ret:
            frames.append(img)

    # convert to numpy
    frames_np = np.array(frames)

    return frames_np


def crop_array(np_array, left=0.0, right=0.0, top=0.0, bottom=0.0):
    """
    Function to crop numpy arrays (4-dim array, crops middle two dimensions)
    :param np_array: input array of dim: AxBx[no. of frames]
    :param top: how many rows from the top will be cropped
    :param bottom: how many rows from the bottom will be cropped
    :param left: how many columns from the left will be cropped
    :param right: how many columns from the right will be cropped
    :return: the de-identified array
    """

    dims = np_array.shape

    assert len(dims) == 4, "Array for cropping has wrong dimensions"

    top = int(np.ceil(dims[1] * top))

    # crop first <crop_from_top> rows
    cropped = np_array[:, top:, :, :]

    return cropped


def export_array_to_video(np_array, save_path="/Users/fryderykkogl/Documents/university/master/thesis/data.nosync/nick/test/IM00001_crop.mov", codec='H264', fps=30):
    """
    Exports numpy array to video
    :param np_array: input array of dim: AxBx[no. of frames]
    :param save_path: Path where the video will be saved (extension included in path)
    :param codec: fourcc codec
    :param fps: Frames per second
    """
    # get images shape
    frame_size = np_array.shape[1:-1]

    # create video writer
    # dimensions have to be inverted for the VideoWriter
    out = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*codec), fps, frame_size[::-1], isColor=True)

    # loop through all frames and write them to the video writer
    for i in range(np_array.shape[0]):
        img = np_array[i, :, :, :]  # .astype('uint8')
        out.write(img)

    # release the writer
    out.release()


def one_video(video_path, save_path):
    """
    Takes in one video path and saves it cropped to the save path
    :param video_path:
    :param save_path:
    """
    # get data array as numpy array
    us_numpy = load_video_to_numpy(video_path)

    # deidentify by cropping
    us_numpy_cropped = crop_array(us_numpy.copy(), top=0.09166)

    # create video
    export_array_to_video(us_numpy_cropped, save_path=save_path)


def run_export_main(params):
    # get paths
    assert params.load_path.lower().endswith(".mov") or params.load_path.lower().endswith(".mp4"), "File has to be .mov or .mp4"
    load_path = params.load_path
    if load_path.lower().endswith(".mov"):
        save_path = load_path.replace(".mov", "_crop.mp4")
    else:
        save_path = load_path.replace(".mp4", "_crop.mp4")

    # set up logging
    if load_path.lower().endswith(".mov"):
        logging.basicConfig(filename=load_path.lower().replace(".mov", ".log"))
    else:
        logging.basicConfig(filename=load_path.lower().replace(".mp4", ".log"))
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    try:
        one_video(load_path, save_path)

    except Exception as e:
        logger.error(f"could not process {load_path}.\n{str(e)}")
        raise f"could not process {load_path}.\n{str(e)}"


class GUIWindow:
    def __init__(self,):
        dpg.create_context()
        dpg.create_viewport(title='', width=600, height=300)

        self.load_paths = ""

        self.export_handler = ExportHandling()

    def crop_callback(self):

        # convert string into a list
        path_list = []
        for path in self.load_paths.splitlines():
            path_list.append(path)

        self.export_handler.run_export_main(path_list)

    def _log(self, sender, app_data, user_data):
        self.load_paths = app_data

    def main(self):
        with dpg.window(label="Crop files"):
            dpg.add_button(label="Crop", callback=self.crop_callback)

            dpg.add_text("\nAdd paths to the files that you want to convert:\n"
                         "NOTES:\n"
                         "\t- each path has to be in a new line\n"
                         "\t- each cropped file is saved in the same directory as the original file\n"
                         "\t- the error log is saved in the directory where the first file is saved\n"
                         "\t- the amount of pixels cropped is fixed - it is dialed in for clips such as lung US")
            dpg.add_input_text(label="", callback=self._log, multiline=True)

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()



#
# if __name__ == "__main__":
#     parser = argparse.ArgumentParser()
#
#     parser.add_argument("-lp", "--load_path", type=str, required=True,
#                         help="Path to the .dicom file to be de-identified")
#
#     arguments = parser.parse_args()
#
#     main(arguments)
