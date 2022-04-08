import argparse

from logic import FileInspector
from paths import paths


def main(params):

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
