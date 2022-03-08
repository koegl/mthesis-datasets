from deidentify_mp4.main_func import main
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-lp", "--load_path", type=str, required=True,
                        help="Path to the .dicom file to be de-identified")

    arguments = parser.parse_args()

    main(arguments)
