import argparse
import numpy as np
import utils
import os
import warnings


# script to compare coordinates from two sets of coordinates from one file
# CONCLUSION - in RESECT the first and second set are not just shifted, they are misaligned
def main(params):

    # find tag file(s)
    tag_paths = []

    if params.file_path is not None:
        tag_paths = [params.file_path]

    elif params.directory is not None:
        # find all .tag files
        for path, _, files in os.walk(params.directory):
            for name in files:
                if name.endswith('.tag'):
                    tag_paths.append(os.path.join(path, name))

    else:
        warnings.warn("No path(s) specified. Exiting.")
        return

    for tag_file in tag_paths:
        coors = utils.read_tag_file(tag_file)

        # loop through all sets of points
        for i in range(len(coors)):
            # calculate distances between landmarks
            p1 = coors[i, 0:3]
            p2 = coors[i, 3:6]
            print(utils.euclid_dist(p1, p2))

        print(5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--directory", type=str, default=None, help="Path to the directory in which all .tag files will be"
                                                            "converted to .fcsv")
    parser.add_argument("-fp", "--file_path", type=str, default=None, help="File path of the file to be displayed")

    arguments = parser.parse_args()

    main(arguments)
