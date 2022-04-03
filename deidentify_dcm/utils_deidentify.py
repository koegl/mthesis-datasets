import os


def extract_file_paths(parent_folder_path, extension=""):
    """
    Extract all file paths from the folder, subfolders etc. of the given extension. Empty extension ("") means .dcm
    :param parent_folder_path: Path to the parent folder
    :param extension: Extension of the files to be extracted
    :return: list of all file paths
    """
    # todo add gui option to specify the extension
    # get all files
    all_files_buf = []
    for root, _, files in os.walk(parent_folder_path):
        for file in files:
            buf_path = os.path.join(root, file)

            # check for correct extension
            buf_file_name = os.path.basename(buf_path)
            file_name_split = buf_file_name.split(".")

            if len(file_name_split) == 1:  # it's a dicom without an extension
                current_extension = ""
            else:
                current_extension = file_name_split[1]

            if "ds_store" not in buf_path.lower() and "dicomdir" not in buf_path.lower() and \
                    (current_extension == "" or current_extension == "mp4" or current_extension == "mov" or
                     current_extension == "avi"):
                all_files_buf.append(buf_path)

    return all_files_buf
