import os
import numpy as np


def extract_features(file_path):
    """
    Extracts features from a file.
    @param file_path: Path to the niftii file.
    @return: The file path to the extracted features.
    """

    file_features_path = file_path.split('.')[0] + '_features.key'

    # todo add check what machine is running the script
    command = f"./sift_executables/featExtract.mac -qto_xyz \"{file_path}\" \"{file_features_path}\""
    os.system(command)

    return file_features_path


def match_features(feature1_path, feature2_path):
    """
    Mathc features between two .key files
    @param feature1_path: Path to the first .key file
    @param feature2_path: Path to the second .key file
    @return: the matched features
    """

    # todo add check what machine is running the script
    command = f"./sift_executables/featMatchMultiple.mac \"{feature1_path}\" \"{feature2_path}\""
    os.system(command)

    # load features from 1st file
    matched1_path = feature2_path + ".matches.img1.txt"
    matched1 = read_matched_features(matched1_path)

    matched2_path = feature2_path + ".matches.img2.txt"
    matched2 = read_matched_features(matched2_path)

    # delete files created by featMatchMultiple.mac
    remove_files_created_by_matching(matched1_path, matched2_path)

    return matched1, matched2


def remove_files_created_by_matching(matched1_path, matched2_path):
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


def read_matched_features(matched_path):
    """
    Reads the matched features from a .key file
    @param matched_path: Path to the .key file
    @return: The matched features
    """

    with open(matched_path, 'r') as f:
        lines = f.readlines()

    # remove header
    lines = lines[4:]

    # split lines by tab
    lines = [x.split('\t') for x in lines]

    # remove file name, scale and the ends
    lines = [x[2:5] for x in lines]

    # convert to float
    lines = [[float(x) for x in y] for y in lines]

    # convert to numpy array
    features = np.asarray(lines)

    return features


def write_features_to_fcsv(features, fcsv_path):
    """
    Writes features to a .fcsv file
    @param features: The features
    @param fcsv_path: The path to the .fcsv file
    """

    # create string to write
    text = ""

    shape = features.shape
    for i in range(shape[0]):

        text += str(i+1) + ","

        for j in range(shape[1]):
            text += str(features[i, j]) + ','

        text += f"0,0,0,1,1,1,0,F_{i+1},,,,2,0\n"
        
    with open(fcsv_path, 'w') as f:
        f.write(text)
