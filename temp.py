import argparse
import sys


def main(params):
    print(params.load_path)
    print(params.load_path)
    print(params.load_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-lp", "--load_path", type=str, help="Path to the .dicom file to be de-identified")

    arguments = parser.parse_args()

    if len(sys.argv) < 2:
        parser.print_usage()
        sys.exit(1)

    main(arguments)