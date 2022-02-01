import argparse
import numpy as np
import utils
import os


# script to convert all .tag files into two .fcsv files in a given directory and al its subdirectories
def main(params):

    # find all .tag files
    for path, _, files in os.walk(params.directory):
        for name in files:
            if name.endswith('.tag'):
                tag_path = os.path.join(path, name)

                # convert file into .fscv
                utils.tag2fcsv(tag_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--directory", type=str, help="Path to the directory in which all .tag files will be"
                                                            "converted to .fcsv")

    arguments = parser.parse_args()

    main(arguments)
