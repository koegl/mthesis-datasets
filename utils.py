import matplotlib.pyplot as plt
import numpy as np
import os


def volumetric_plot(image, volume_type="label", threshold=0.1):
    """
    Make an interactive volumetric plot
    :param image: The image to be displayed (numpy array)
    :param volume_type: This will be shown as the title of the plot
    :param threshold: The image needs to be binary
    """

    # make binary
    image[image < threshold] = 0
    image[image >= threshold] = 1

    # volumetric visualisation
    voxels = image.astype(bool)
    colors = np.empty(voxels.shape, dtype=object)
    colors[voxels] = 'red'

    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.voxels(voxels, facecolors=colors, edgecolor='none')

    ax.set_title(volume_type)

    plt.show()


def is_float(word):
    """
    Chechs if the function argument (which is a string) represents a float. If yes, it returns True, otherwise False
    :param word: A string which will be inspected
    :return: True or False
    """
    try:
        float(word)
        return True

    except ValueError:
        return False


def read_tag_file(tag_file_path):
    """
    Reads a .tag file into a 6xN numpy array, where N is the amount of point pairs
    :param tag_file_path: Path to the tag file
    :return: numpy array containing the points
    """
    # read text into one string
    with open(tag_file_path) as file:
        text = file.read()

    # split string at spaces
    text = text.split(" ")

    # remove everything before the 'Points' keyword
    for i, value in enumerate(text):
        if text[i] == "Points":
            words = text[i+3:]
            break

    # convert the rest to numbers (only numbers, disregard strings)
    numbers = [float(x) for x in text if is_float(x)]

    # convert to 2D array
    coordinates = np.asarray(numbers)

    coordinates = coordinates.reshape((int(len(numbers)/6), 6))

    return coordinates


def write_fcsv_files(point_array, tag_file_path):
    """
    Write a 2D array of point pairs into two .fcsv files - the first one containing the first set of points, the second
    one containing the second set of points
    :param point_array: 6xN numpy array, where N is the amount of point pairs
    :param tag_file_path: path of the .tag file from which the data was read
    """

    for suffix in ['_first', '_second']:

        # open new .fcsv file
        with open(os.path.splitext(tag_file_path)[0] + suffix + '.fcsv', "a") as file:

            # write the header
            file.write("# Markups fiducial file\n")
            file.write("# CoordinateSystem = LPS\n")
            file.write("# columns = id,x,y,z,ow,ox,oy,oz,vis,sel,lock,label,desc,associatedNodeID\n")

            amount_of_pairs = len(point_array.flatten()) / 6

            # loop through coordinates (amount of pairs)
            for i in range(int(amount_of_pairs)):

                # ID
                file.write(str(i) + ",")

                # point
                if suffix == '_first':
                    offset = 0
                else:
                    offset = 3

                # loop through x,y,z coordinates
                for j in range(3):
                    file.write(str(point_array[i, j + offset]) + ",")

                # quaternion
                file.write("0,0,0,1,")

                # visibility
                file.write("1,")

                # selected flag
                file.write("1,")

                # locked flag
                file.write("0,")

                # label
                file.write("F-" + str(i+1) + ",,\n")


def tag2fcsv(tag_file_path):
    """
    Convert a .tag file to two .fcsv file - one containing the first set of coordinates, the other the second set of
    coordinates
    :param tag_file_path: Path to the .tag file
    """

    # read coordinates into a numpy array
    coordinate_pairs = read_tag_file(tag_file_path)

    # write coordinate pairs into two .fcsv files
    write_fcsv_files(coordinate_pairs, tag_file_path)