import cv2
import numpy as np
import argparse


def export_array_to_video(np_array, save_path='/Users/fryderykkogl/Desktop/output_video.mp4', codec='MP4V', fps=24):
    """
    Exports numpy array to video
    :param np_array: input array of dim: AxBx[no. of frames]
    :param save_path: Path where the video will be saved (extension included in path)
    :param codec: fourcc codec
    :param fps: Frames per second
    """

    # get images shape
    frame_size = np_array.shape[0:2]

    # create video writer
    out = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*codec), fps, frame_size, isColor=False)

    # loop through all frames and write them to the video writer
    for i in range(np_array.shape[-1]):
        img = np.ones((500, 500), dtype=np.uint8) * i
        out.write(img)

    # release the writer
    out.release()


def main(params):
    print(5)


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
