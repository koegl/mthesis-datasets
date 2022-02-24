import cv2
from pydicom import dcmread, read_file


def export_array_to_video(np_array, save_path='/Users/fryderykkogl/Desktop/output_video.mp4', codec='MP4V', fps=24):
    """
    Exports numpy array to video
    :param np_array: input array of dim: AxBx[no. of frames]
    :param save_path: Path where the video will be saved (extension included in path)
    :param codec: fourcc codec
    :param fps: Frames per second
    """

    # get images shape
    frame_size = np_array.shape[1:]

    # create video writer
    out = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*codec), fps, frame_size[::-1], isColor=False)

    # loop through all frames and write them to the video writer
    for i in range(np_array.shape[0]):
        img = np_array[i, :, :]
        out.write(img)

    # release the writer
    out.release()


def deidentify_us_images(np_array, black_from_top=0):
    """
    Function to de-identify (make top x rows black) US images
    :param np_array: input array of dim: AxBx[no. of frames]
    :param black_from_top: how many rows from the top will be made black
    :return: the de-identified array
    """

    # make first <crop_from_top> rows black
    # todo check which dimension should be balcked out
    np_array[:, 0:black_from_top, :] = 0

    return np_array


def load_dicom_to_numpy(dicom_path='CT_small.dcm'):
    """
    Function to load DICOMs and return the data as a numpy array of shape AxBx[no. of frames]
    :param dicom_path: Path to the DICOM
    :return: The numpy array with the data from DICOM
    """

    # read dicom
    # fpath = get_testdata_file(dicom_path)
    ds = read_file(dicom_path)

    # return only the pixel values as a numpy array
    return ds.pixel_array


def main(params):

    us_numpy = load_dicom_to_numpy("/Users/fryderykkogl/Downloads/bmode.dcm")

    # todo this is only temporrary for this dicom
    us_numpy = us_numpy[:, :, :, 0]

    us_numpy_deidentified = deidentify_us_images(us_numpy.copy(), black_from_top=100)

    export_array_to_video(us_numpy_deidentified, save_path='/Users/fryderykkogl/Desktop/output_video_ori.mp4')


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
