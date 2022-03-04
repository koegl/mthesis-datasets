import os


def extract_mrb_paths(directory_path="/Users/fryderykkogl/Dropbox (Partners HealthCare)/TCIA/TCIA cases ALL"):
    """
    Function to extract all .mrb files from a directory and its sub-directories
    @param directory_path: Path to the root directory
    @return: a list of all paths
    """
    mrb_paths = []

    for path, subdirs, files in os.walk(directory_path):
        for name in files:
            if ".mrb" in name:
                mrb_paths.append(os.path.join(path, name))

    return mrb_paths
