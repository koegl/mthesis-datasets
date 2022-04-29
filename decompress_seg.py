import os
import pydicom
import sys


# get all files from directory and subdirectory
def get_all_files(path):
    files = []
    for root, dirs, file_names in os.walk(path):
        for file_name in file_names:
            files.append(os.path.join(root, file_name))
    return files


def main():
    # get all files
    files = get_all_files(sys.argv[1])
    ds = None
    # loop through all files
    for file in files:
        # read dicom file
        try:
            ds = pydicom.dcmread(file)

            if ds.Modality.lower() == 'seg':
                # execute dcmdrle in shell
                os.system(f"dcmdrle \"{file}\" \"{file}_decompressed\"")

        except Exception as e:
            continue


if __name__ == "__main__":
    main()
