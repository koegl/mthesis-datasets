import os
import cv2
import numpy as np


# function to load a mp4 file and return the frames
def load_mp4(path, subsample=False):
    """
    Function to load an mp4 file and return the frames as a numpy array
    @param path: path to the mp4 file
    @param subsample: if True, subsample the frames to 1/4th of the original size
    @return:
    """
    cap = cv2.VideoCapture(path)

    frames = []

    ret = True

    while ret:
        ret, img = cap.read()  # read one frame from the 'capture' object; img is (H, W, C)
        if ret:
            frames.append(img)

    cap.release()

    # convert to numpy
    frames_np = np.array(frames)

    if subsample:
        if len(frames_np.shape) == 4:
            frames_np = frames_np[:, ::subsample, ::subsample, :]
        elif len(frames_np.shape) == 3:
            frames_np = frames_np[:, ::subsample, ::subsample]

    return frames_np


def extract_file_paths_with_extension(parent_folder_path, extension="", exclude=None):
    """
    Extract all file paths from the folder, sub-folders etc. of the given extension. Empty extension ("") means .dcm
    :param parent_folder_path: Path to the parent folder
    :param extension: Extension of the files to be extracted
    :param exclude: keyword in path that would exclude the file from the list
    :return: list of all file paths
    """

    # get all files
    all_files_buf = []
    for root, _, files in os.walk(parent_folder_path):
        for file in files:
            buf_path = os.path.join(root, file)

            # check for correct extension
            buf_file_name = os.path.basename(buf_path)
            file_name_split = buf_file_name.split(".")

            if len(file_name_split) == 1:  # it's a dicom without an extension
                current_extension = ""
            else:
                current_extension = file_name_split[1]

            if "ds_store" not in buf_path.lower() and "dicomdir" not in buf_path.lower() and \
                    current_extension == extension:

                if exclude:
                    if exclude not in buf_path.lower():
                        all_files_buf.append(buf_path)
                else:
                    all_files_buf.append(buf_path)

    all_files_buf.sort()

    return all_files_buf
