import os
from pathlib import Path
import numpy as np
from pydicom.pixel_data_handlers.util import _convert_YBR_FULL_to_RGB
from pydicom import read_file
import logging.config
import cv2
from tqdm import tqdm


class DicomToMp4Crop:
    @staticmethod
    def load_dicom_to_numpy_and_fps(dicom_path='CT_small.dcm'):
        """
        Function to load DICOMs and return the data as a numpy array of shape AxBx[no. of frames]
        :param dicom_path: Path to the DICOM
        :return: The numpy array with the data from DICOM and the frame rate
        """
        # read dicom
        ds = read_file(dicom_path)

        # return only the pixel values as a numpy array
        pixels = ds.pixel_array

        # convert color space
        if len(pixels.shape) == 4:
            pixels = _convert_YBR_FULL_to_RGB(pixels)

        # get frame rate
        frame_time = ds.FrameTime
        fps = 1000 / frame_time

        return pixels, fps

    @staticmethod
    def load_video_to_numpy_and_fps(video_path="/Users/fryderykkogl/Documents/university/master/thesis/data.nosync/nick/test/IM00001.mov"):
        """
        Function to load a video and return the data as a numpy array
        :param video_path: Path to the .mov
        :return: The numpy array with the data from the video [frames x [dim1, dim2] x 3]
        """
        # todo get frame rate from video
        # extract frames per second from video
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)

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

        return frames_np, fps

    @staticmethod
    def crop_array(np_array, top_percent=0.0, bottom_percent=0.0, left_percent=0.0, right_percent=0.0):
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

        if len(dims) != 4 and len(dims) != 3:
            raise ValueError("Array for cropping has wrong dimensions. (crop_array)")

        # check if not too much would be cropped
        if 0.1 > top_percent >= 0.9 or\
           0.1 > bottom_percent >= 0.9 or\
           0.1 > left_percent >= 0.9 or\
           0.1 > right_percent >= 0.9 or\
           top_percent + bottom_percent >= 0.9 or\
           left_percent + right_percent >= 0.9:
            raise ValueError("Too much cropping, lower the percentages")

        # convert percentages into pixels
        top = int(np.ceil(dims[1] * top_percent))
        bottom = int(np.ceil(dims[1] * bottom_percent))
        left = int(np.ceil(dims[1] * left_percent))
        right = int(np.ceil(dims[1] * right_percent))

        # crop - we need separate cases for rgb and grayscale
        if len(dims) == 4:
            if bottom == 0 and right == 0:
                cropped = np_array[:, top:, left:, :]
            elif bottom == 0 and right != 0:
                cropped = np_array[:, top:, left:-right, :]
            elif bottom != 0 and right == 0:
                cropped = np_array[:, top:-bottom, left:, :]
            else:
                cropped = np_array[:, top:-bottom, left:-right, :]
        else:  # the 4th dimension is usually the rgb value
            if bottom == 0 and right == 0:
                cropped = np_array[:, top:, left:]
            elif bottom == 0 and right != 0:
                cropped = np_array[:, top:, left:-right]
            elif bottom != 0 and right == 0:
                cropped = np_array[:, top:-bottom, left:]
            else:
                cropped = np_array[:, top:-bottom, left:-right]

        return cropped

    @staticmethod
    def export_array_to_video(np_array, save_path='/Users/fryderykkogl/Desktop/output_video.mp4', codec='avc1', fps=26.09):
        """
        Exports numpy array to video
        :param np_array: input array of dim: AxBx[no. of frames]
        :param save_path: Path where the video will be saved (extension included in path)
        :param codec: fourcc codec
        :param fps: Frames per second
        """
        # rgb
        if len(np_array.shape) == 4:
            frame_size = np_array.shape[1:-1]

            buf = np_array.copy()
            np_array[:, :, :, 0] = buf[:, :, :, 2]
            np_array[:, :, :, 2] = buf[:, :, :, 0]

            # create video writer; dimensions have to be inverted for the VideoWriter
            out = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*codec), fps, frame_size[::-1], isColor=True)

            # loop through all frames and write them to the video writer
            for i in range(np_array.shape[0]):
                img = np_array[i, :, :, :].astype('uint8')
                out.write(img)

        # grayscale
        else:
            frame_size = np_array.shape[1:]

            # create video writer; dimensions have to be inverted for the VideoWriter
            out = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*codec), fps, frame_size[::-1], isColor=False)

            # loop through all frames and write them to the video writer
            for i in range(np_array.shape[0]):
                img = np_array[i, :, :].astype('uint8')
                out.write(img)

        # release the writer
        out.release()

    @staticmethod
    def export_array_to_dicom(np_array, save_path):
        """
        Export numpy array to dicom
        :param np_array: input array
        :param save_path: Path where the dicom will be saved (extension included in path)
        :return:
        """
        # todo
        raise NotImplementedError

    def deidentify_one_dicom(self, file_path, save_path, crop_values):
        """
        Takes in one dicom path and saves it as an mp4 to the save path
        :param file_path: Path from where the dicom/mp4 will be loaded
        :param save_path: Path where the video will be stored
        :param crop_values: the amount to be cropped from each side
        """

        # get data array as numpy array
        if file_path.lower().endswith('.mp4') or \
           file_path.lower().endswith('.avi') or \
           file_path.lower().endswith('.mov'):

            us_numpy, fps = self.load_video_to_numpy_and_fps(file_path)
        else:
            us_numpy, fps = self.load_dicom_to_numpy_and_fps(file_path)

        # deidentify by cropping
        us_numpy_cropped = self.crop_array(us_numpy.copy(),
                                           top_percent=crop_values[0],
                                           bottom_percent=crop_values[1],
                                           left_percent=crop_values[2],
                                           right_percent=crop_values[3])

        # create video
        self.export_array_to_video(us_numpy_cropped, fps=fps, save_path=save_path)


class ExportHandling:
    def __init__(self):
        self.dicom_exporter = DicomToMp4Crop()

        self.load_paths = None
        self.logger = None

        self.current_path = None

        # set up logging
        try:
            desktop_path = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
            logging.basicConfig(filename=os.path.join(desktop_path, "deidentify.log"))
        except:
            logging.basicConfig(filename="deidentify.log")

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

    @staticmethod
    def create_save_path(load_path):
        """
        Creates save path and save directory one above the original files. example file name: case-230-001.mp4.
        The de-identified will be in the folder parallel to the dicom image folder
        :param load_path: The load path of the files
        :return: The save path
        """
        # get parent parent
        parent_parent = Path(load_path).parent.parent.absolute()

        # directory with de-identified clips
        save_folder = os.path.join(parent_parent, "DEIDENTIFIED CLIPS")

        if not os.path.exists(save_folder):
            os.makedirs(save_folder)

        # remove potential dicom extension
        buf_file_name = os.path.basename(load_path)
        buf_file_name = buf_file_name.split(".")[0]

        file_name = str(parent_parent).split("/")[-1][0:8].lower() + "-" + buf_file_name[-3:] + ".mp4"

        # get full save path
        save_path = os.path.join(save_folder, file_name)

        return save_path

    def run_export_loop(self, load_paths, crop_values):
        self.load_paths = load_paths

        print("\n\n")

        # export loop
        for i in tqdm(range(len(load_paths)), "Exporting DICOMs to mp4"):
            load_path = load_paths[i]

            # get paths
            assert load_path.lower().endswith(".dcm") or load_path.lower().endswith(""), "File has to be DICOM"

            self.current_path = load_path

            save_path = self.create_save_path(load_path)

            try:
                self.dicom_exporter.deidentify_one_dicom(load_path, save_path, crop_values)

                if not os.path.exists(save_path):
                    self.logger.error(f"could not export {load_path}.")

            except Exception as e:
                self.logger.error(f"could not process {load_path}. {str(e)}")
                continue

        print("\n\n========================================================\n"
              "========================================================\n"
              "Finished exporting\n\n")
