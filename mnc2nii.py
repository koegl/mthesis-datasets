import os
import argparse


# activate minc toolkit - this needs to be done in the terminal manually first
# os.system(". /opt/minc/1.9.18/minc-toolkit-config.sh")

def main(args):

    directory = args.directory

    # get all .mnc files in given directory
    all_files = [os.path.join(path, name) for path, subdirs, files in os.walk(directory) for name in files if ".nii" in name]

    # loop through all .mnc files and convert them to .nii
    for file in all_files:

        # create new filename
        new_file = os.path.splitext(file)[0] + '.nii'

        command = "mnc2nii \"{}\" \"{}\"".format(file, new_file)

        os.system(command)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--directory", type=str, help="Directory in which mnc files will be searched for and"
                                                            "converted to nii")

    arguments = parser.parse_args()

    main(arguments)
