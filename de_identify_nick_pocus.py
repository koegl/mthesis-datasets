# Script to create de-identified mp4
import os

import numpy as np
import logging
import cv2


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


def main():
    folders = [
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/1) 32508822",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/2) 38281101",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/3) 23086077",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/4) 11236528",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/5) 05785175",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/6)41211459",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/7) 09461468",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/8) 39395363-Only a couple Bowel US",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/9) 12796751",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/10) 29109857",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/11) 40341745",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/12) 05723317",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/13) 12678678",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/14) 09521857",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/15) 14807176",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/16) 05890017",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/17) 03786159",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/18) 11136660",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/19) 39084702",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/20) 29983004",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/21) 19066802",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/22) 17106600",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/23) 19941780",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/24) 22151237",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/25)01851518",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/26) 33887084",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/27) 16682700",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/28) 30205330",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/29) 21173117",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/30) 21433933",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/31) 38472981",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/32) 30406920",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/33) 15050131",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/34) 09894437",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/35) 35362185",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/36) 29501939",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/37) 09624750",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/38) 14207443",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/39) 34263038-half scans are Bowel",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/40) 14263867",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/41) 16938078",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/42) 10826592",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/43) 10540979",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/44) 28933448",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/45) 35015031",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/46) 28912376",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/47) 22880579",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/48) 33617853",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/49) 21762596",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/50) 35943638",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/51) 36159887",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/52) 12472833-Different Date",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/53) 12472833",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/54) 04731766",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/55) 33768482",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/56) 10332021",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/57) 10097160",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/58) 04475257",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/59) 32329492",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/60) 35768993",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/61) 17492323",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/62) 28912376-Different Date",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/63) 25441072",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/64) 28912376-Third Time",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/65) 28912376-Fourth Time",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/66) 13375001",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/67) 31825524",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/68) 27666437",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/69) 19911759",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/70) 03786159-Different Date",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/71) 24284150",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/72) 06050017",
        "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS SBO Scans/73) 30184972",
    ]
    folders.sort()

    logging.basicConfig(filename="/Users/fryderykkogl/Desktop/pocus_log.log")
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    base_export_folder = "/Users/fryderykkogl/Dropbox (Partners HealthCare)/Nick-Fryderyk Shared Folder/POCUS_deidentified_by_F"

    for folder in folders:
        try:
            # logger.debug(f"{folder}")

            # get case and ID
            case_id_folder = os.path.basename(folder)

            # get clips folder
            clips_folder = [x[0] for x in os.walk(folder) if "CLIPS" in x[0]]

            if not clips_folder:  # if it's empty
                continue

            # loop through all clips for processing
            for clip in os.listdir(clips_folder[0]):

                # create save path
                if not os.path.exists(os.path.join(base_export_folder, case_id_folder)):
                    os.makedirs(os.path.join(base_export_folder, case_id_folder))

                save_path = os.path.join(base_export_folder, case_id_folder, clip)
                save_path = save_path.replace(".mov", "_crop.mov")

                load_path = os.path.join(clips_folder[0], clip)

                try:
                    one_video(load_path, save_path)
                    # logger.info(save_path)
                except Exception as e:
                    logging.error(f"could not process file {save_path}.\n{str(e)}")

        except Exception as e:
            logger.error(f"could not process a file in {folder}.\n{str(e)}")


if __name__ == "__main__":
    main()
