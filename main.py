import os
import numpy as np
import argparse
from time import perf_counter

from utils import extract_features, match_features, write_features_to_fcsv


def main(args):

    file1_path = args.file_1
    file2_path = args.file_2

    # extract features
    start_time = perf_counter()
    # file1_features_path = extract_features(file1_path)
    # file2_features_path = extract_features(file2_path)
    end_time = perf_counter()
    print(f"\nFeature extraction time: {end_time - start_time}\n")

    # feature matching
    start_time = perf_counter()
    file1_features_path = "/Users/fryderykkogl/Data/nifti_test/785522447/Intra-op US/US1_features.key"
    file2_features_path = "/Users/fryderykkogl/Data/nifti_test/785522447/Intra-op US/US2_features.key"
    features = match_features(file1_features_path, file2_features_path)
    end_time = perf_counter()
    print(f"\nFeature matching time: {end_time - start_time}\n")

    # convert features to .fcsv
    write_features_to_fcsv(features[0], file1_path.split(".")[0] + ".fcsv")
    write_features_to_fcsv(features[1], file2_path.split(".")[0] + ".fcsv")


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("-f1", "--file_1", type=str, default=None, help="First nifti file path")
    parser.add_argument("-f2", "--file_2", type=str, default=None, help="Second nifti file path")

    arguments = parser.parse_args()

    main(arguments)
