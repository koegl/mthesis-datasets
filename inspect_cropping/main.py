import argparse

from logic import FileInspector
import json


def main(params):

    # read json file from paths_path
    paths_path = "/Users/fryderykkogl/Data/deidentify/paths.json"
    with open(paths_path) as json_file:
        paths = json.load(json_file)
        paths = paths["paths"]

    inspector = FileInspector(paths, extension="mp4")

    inspector.inspect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-md", "--main_directory", default="/Users/fryderykkogl/Dropbox (Partners HealthCare)/MLSC "
                                                           "Data/MLSC Data with PHI for BWH "
                                                           "only/Lung/Case-499-00568797",
                        help="Path to the fixed image")

    args = parser.parse_args()

    main(args)
