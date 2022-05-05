import os
import numpy as np
import argparse
from time import perf_counter

from utils import extract_features, match_features


def main(args):

    file1_path = args.file_1
    file2_path = args.file_2

    # extract features
    start_time = perf_counter()
    file1_features_path = extract_features(file1_path)
    file2_features_path = extract_features(file2_path)
    end_time = perf_counter()
    print(f"\nFeature extraction time: {end_time - start_time}\n")

    # feature matching

    start_time = perf_counter()
    match_features(file1_features_path, file2_features_path)
    end_time = perf_counter()
    print(f"\nFeature matching time: {end_time - start_time}\n")



if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("-f1", "--file_1", type=str, default=None, help="First nifti file path")
    parser.add_argument("-f2", "--file_2", type=str, default=None, help="Second nifti file path")

    arguments = parser.parse_args()

    main(arguments)
