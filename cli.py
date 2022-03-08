from deidentify_mp4.__main__ import main
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-p", "--path", type=str, help="Path to the .dicom file to be de-identified")

    arguments = parser.parse_args()

    main(arguments)
