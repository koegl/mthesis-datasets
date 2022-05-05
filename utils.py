import os
import numpy as np


def extract_features(file_path):
    """
    Extracts features from a file.
    @param file_path: Path to the niftii file.
    @return: The file path to the extracted features.
    """

    file_features_path = file_path.split('.')[0] + '_features.key'

    command = f"./featExtract.mac \"{file_path}\" \"{file_features_path}\""
    os.system(command)

    return file_features_path


def match_features(feature1_path, feature2_path):
    """
    Mathc features between two .key files
    @param feature1_path: Path to the first .key file
    @param feature2_path: Path to the second .key file
    @return: the matched features
    """

    command = f"./featMatchMultiple.mac \"{feature1_path}\" \"{feature2_path}\""
    os.system(command)

    # load features from 1st file
    matched1_path = feature2_path + ".matches.img1.txt"
    matched1 = read_matched_features(matched1_path)

    matched2_path = feature2_path + ".matches.img2.txt"
    matched2 = read_matched_features(matched2_path)

    # delete files created by featMatchMultiple.mac
    os.remove(matched1_path)
    os.remove(matched2_path)
    path = matched2_path[:-8] + "info.txt"
    os.remove(path)
    path = matched2_path[:-16] + "trans-inverse.txt"
    os.remove(path)
    path = matched2_path[:-16] + "trans.txt"
    os.remove(path)
    path = matched2_path[:-16] + "update.key"
    os.remove(path)

    return matched1, matched2


def read_matched_features(matched_path):
    """
    Reads the matched features from a .key file
    @param matched_path: Path to the .key file
    @return: The matched features
    """

    with open(matched_path, 'r') as f: