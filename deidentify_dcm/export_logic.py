import os
from pathlib import Path
import numpy as np
from pydicom.pixel_data_handlers.util import _convert_YBR_FULL_to_RGB
from pydicom import read_file
import logging.config
import cv2


class ExportHandling:
    def __init__(self):
        self.load_paths = None
        self.logger = None
        self.crop_values = [0.0, 0.0, 0.0, 0.0]

    def load_dicom_to_numpy(self, dicom_path='CT_small.dcm'):
        """
        Function to load DICOMs and return the data as a numpy array of shape AxBx[no. of frames]
        :param dicom_path: Path to the DICOM
        :return: The numpy array with the data from DICOM
        """

        # read dicom
        ds = read_file(dicom_path)

        # return only the pixel values as a numpy array
        pixels = ds.pixel_array

        # convert color space
        pixels = _convert_YBR_FULL_to_RGB(pixels)

        return pixels

    def crop_array(self, np_array, top_percent=0.0, bottom_percent=0.0, left_percent=0.0, right_percent=0.0):
        """
        Function to de-identify (crop top x rows) US images
        :param np_array: input array of dim: AxBx[no. of frames]
        :param top_percent: how many percent rows will be cropped
        :param bottom_percent: how many percent rows will be cropped
        :param left_percent: how many percent rows will be cropped
        :param right_percent: how many percent rows will be cropped
        :return: the de-identified array
        """

        dims = np_array.shape

        if len(dims) != 4:
            raise Exception("Array for cropping has wrong dimensions")

        # check if not too much would be cropped
        if 0.1 > top_percent >= 0.9 or\
           0.1 > bottom_percent >= 0.9 or\
           0.1 > left_percent >= 0.9 or\
           0.1 > right_percent >= 0.9 or\
           top_percent + bottom_percent >= 0.9 or\
           left_percent + right_percent >= 0.9:
            raise Exception("Too much cropping, lower the percentages")

        # convert percentages into pixels
        top = int(np.ceil(dims[1] * top_percent))
        bottom = int(np.ceil(dims[1] * bottom_percent))
        left = int(np.ceil(dims[1] * left_percent))
        right = int(np.ceil(dims[1] * right_percent))

        # crop - we need separate cases because one cannot crop to :-0
        if bottom == 0 and right == 0:
            cropped = np_array[:, top:, left:, :]
        elif bottom == 0 and right != 0:
            cropped = np_array[:, top:, left:-right, :]
        elif bottom != 0 and right == 0:
            cropped = np_array[:, top:-bottom, left:, :]
        else:
            cropped = np_array[:, top:-bottom, left:-right, :]

        return cropped

    def export_array_to_video(self, np_array, save_path='/Users/fryderykkogl/Desktop/output_video.mp4', codec='H264', fps=26.09):
        """
        Exports numpy array to video
        :param np_array: input array of dim: AxBx[no. of frames]
        :param save_path: Path where the video will be saved (extension included in path)
        :param codec: fourcc codec
        :param fps: Frames per second
        """
        # get images shape
        frame_size = np_array.shape[1:-1]

        # # todo check if this is needed: rgb to bgr
        buf = np_array.copy()
        np_array[:, :, :, 0] = buf[:, :, :, 2]
        np_array[:, :, :, 2] = buf[:, :, :, 0]

        # create video writer; dimensions have to be inverted for the VideoWriter
        out = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*codec), fps, frame_size[::-1], isColor=True)

        # loop through all frames and write them to the video writer
        for i in range(np_array.shape[0]):
            img = np_array[i, :, :, :].astype('uint8')
            out.write(img)

        # release the writer
        out.release()

    def export_array_to_dicom(self):
        # todo
        pass

    def deidentify_one_dicom(self, dicom_path, save_path):
        """
        Takes in one dicom path and saves it as an mp4 to the save path
        :param dicom_path:
        :param save_path:
        """

        # get data array as numpy array
        us_numpy = self.load_dicom_to_numpy(dicom_path)

        # deidentify by cropping
        us_numpy_cropped = self.crop_array(us_numpy.copy(),
                                           top_percent= self.crop_values[0],
                                           bottom_percent=self.crop_values[1],
                                           left_percent=self.crop_values[2],
                                           right_percent=self.crop_values[3])

        # create video
        self.export_array_to_video(us_numpy_cropped, save_path=save_path)

    def run_export_loop(self, load_paths, crop_values):
        self.crop_values = crop_values
        self.load_paths = load_paths

        # set up logging
        split_path_log = load_paths[0].split(".")
        logging.basicConfig(filename=split_path_log[0].lower() + ".log")
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

        # export loop
        for load_path in load_paths:
            # get paths
            assert load_path.lower().endswith(".dcm") or load_path.lower().endswith(""), "File has to be DICOM"

            split_path = load_path.split(".")
            save_path = split_path[0] + "_crop.mp4"

            try:
                self.deidentify_one_dicom(load_path, save_path)

                if not os.path.exists(save_path):
                    self.logger.error(f"could not export {load_path}.")

            except Exception as e:
                self.logger.error(f"could not process {load_path}.\n{str(e)}")
                raise f"could not process {load_path}.\n{str(e)}"