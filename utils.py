
def extract_features(file_path):
    """
    Extracts features from a file.
    @param file_path: Path to the niftii file.
    @return: The file path to the extracted features.
    """

    file_features_path = file_path.split('.')[0] + '_features.key'

    command = f"./featExtract.mac \"{file_path}\" \"{file_features_path}\""
    os.system(command)

    return file_features_path