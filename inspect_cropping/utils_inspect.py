import os
import cv2
import numpy as np


# function to load a mp4 file and return the frames
def load_mp4(path):
    """
    Function to load an mp4 file and return the frames as a numpy array
    @param path:
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

    return frames_np
