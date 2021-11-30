import os
import argparse


# activate minc toolkit - this needs to be done in the terminal manually first:
# . /opt/minc/1.9.18/minc-toolkit-config.sh
# (or locally on F's machine: activateMinc)

def main(args):
    directory = args.directory
    key = args.exclude_keyword

    # get all .mnc files in given directory with the keyword exclusion
    all_files = []

    if key is none:
        for path, subdirs, files in os.walk(directory):
            for name in files:
                if ".mnc" in name:
                    all_files.append(os.path.join(path, name))
    else:
        for path, subdirs, files in os.walk(directory):
            for name in files:
                if ".mnc" in name and key not in name:
                    all_files.append(os.path.join(path, name))

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
    parser.add_argument("-ek", "--exclude_keyword", type=str, default=None, help="If this keyword will be found in the"
                                                                                 "path/filename, then the file will be"
                                                                                 "excluded from conversion")

    arguments = parser.parse_args()

    main(arguments)
