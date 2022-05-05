
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
def read_matched_features(matched_path):
    """
    Reads the matched features from a .key file
    @param matched_path: Path to the .key file
    @return: The matched features
    """

    with open(matched_path, 'r') as f: