import numpy as np
import argparse
import matplotlib.pyplot as plt


def main(args):

    path = args.file_path

    print(path)

    image = np.random.random((100, 100))

    plt.imshow(image)
    plt.show()


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--directory", type=str, default=None, help="Directory in which mnc files will be"
                                                                          "searched for and converted to nii")
    parser.add_argument("-fp", "--file_path", type=str, default=None, help="File path of the file to be displayed")

    arguments = parser.parse_args()

    main(arguments)
