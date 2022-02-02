try:
    import pandas as pd
except:
    slicer.util.pip_install('library_name')
    import pandas as pd


def replace_character_in_file(path_to_file, old_character, new_character):
    """
    :param path_to_file: File to be edited
    :param old_character: The character that will be replaced
    :param new_character: The replacement character
    """

    # read in text and replace in the string
    with open(path_to_file, 'r') as f:
        text = f.read()
        text = text.replace(old_character, new_character)

    # clear file and write the string to it
    with open(path_to_file, 'w+') as f:
        f.truncate(0)
        f.write(text)


def get_max_lengths_of_data_arrays(data_dict: dict) -> dict:
    """
    Takes a patient summary dict and returns a dict with the max max_lengths for each data array
    :param data_dict: The summary dict
    :return: The max_lengths dict
    """

    max_lengths = {"pre_op_im": 0, "intra_us": 0, "intra_rest": 0, "tracking_pre": 0, "tracking_post": 0, "seg_fmir": 0,
                   "seg_dti": 0, "seg_rest": 0}

    for key, item in data_dict.items():
        # data_matrix[0].append(key)
        if len(item["pre-op imaging"]) > max_lengths["pre_op_im"]:
            max_lengths["pre_op_im"] = len(item["pre-op imaging"])
        if len(item["intra-op imaging"]["ultrasounds"]) > max_lengths["intra_us"]:
            max_lengths["intra_us"] = len(item["intra-op imaging"]["ultrasounds"])
        if len(item["intra-op imaging"]["rest"]) > max_lengths["intra_rest"]:
            max_lengths["intra_rest"] = len(item["intra-op imaging"]["rest"])
        if len(item["continuous tracking data"]["pre-imri tracking"]) > max_lengths["tracking_pre"]:
            max_lengths["tracking_pre"] = len(item["continuous tracking data"]["pre-imri tracking"])
        if len(item["continuous tracking data"]["post-imri tracking"]) > max_lengths["tracking_post"]:
            max_lengths["tracking_post"] = len(item["continuous tracking data"]["post-imri tracking"])
        if len(item["segmentations"]["pre-op fmri segmentations"]) > max_lengths["seg_fmir"]:
            max_lengths["seg_fmir"] = len(item["segmentations"]["pre-op fmri segmentations"])
        if len(item["segmentations"]["pre-op brainlab manual dti tractography segmentations"]) > max_lengths["seg_dti"]:
            max_lengths["seg_dti"] = len(item["segmentations"]["pre-op brainlab manual dti tractography segmentations"])
        if len(item["segmentations"]["rest"]) > max_lengths["seg_rest"]:
            max_lengths["seg_rest"] = len(item["segmentations"]["rest"])

    return max_lengths


def create_empty_data_matrix(data_summary_length, max_array_lengths_sum):
    """
    Create an empty data matrix that will be written to an excel spreadsheet
    :param data_summary_length: Amount of different patients
    :param max_array_lengths_sum: The sum of all the maximal lengths of the data arrays
    :return:
    """

    data_summary_length += 2  # '+ 2' for volume type and empty column at the back to stop spill
    max_array_lengths_sum += 10  # '+ 10' for titles, paths and empty rows

    empty_data_matrix = []

    for i in range(data_summary_length):  # '+2' for volume type and empty column
        empty_data_matrix.append([])
        for j in range(max_array_lengths_sum + 10):  # '+1' for titles and paths
            empty_data_matrix[i].append(' ')

    return empty_data_matrix


def fill_empty_matrix_with_summary_dict(summary_dict, data_matrix, max_lengths_dict):
    """
    Fill the empty data matrix with all the values from the summary dict
    :param summary_dict: The dict containing all the summarised patient data
    :param data_matrix: The empty data matrix that will be filled
    :param max_lengths_dict: The dict containing the max lengths of the data arrays
    :return: The filled data_matrix
    """

    id_index = 1
    row_index = 2

    for key, value in summary_dict.items():
        data_matrix[id_index][row_index - 2] = key
        data_matrix[id_index][row_index - 1] = value["path"][0]

        data_matrix[0][row_index + 1] = "pre-op imaging"
        data_matrix[id_index][row_index + 1:row_index + 1 + len(value["pre-op imaging"])] = value["pre-op imaging"]
        row_index += max_lengths_dict["pre_op_im"] + 1

        data_matrix[0][row_index + 1] = "intra-op US"
        data_matrix[id_index][row_index + 1:row_index + 1 + len(value["intra-op imaging"]["ultrasounds"])] = \
            value["intra-op imaging"]["ultrasounds"]
        row_index += max_lengths_dict["intra_us"] + 1
        data_matrix[0][row_index + 1] = "intra-op REST"
        data_matrix[id_index][row_index + 1:row_index + 1 + len(value["intra-op imaging"]["rest"])] = \
            value["intra-op imaging"]["rest"]
        row_index += max_lengths_dict["intra_rest"] + 1

        data_matrix[0][row_index + 1] = "tracking PRE"
        data_matrix[id_index][row_index + 1:row_index + 1 + len(value["continuous tracking data"]["pre-imri tracking"])] \
            = value["continuous tracking data"]["pre-imri tracking"]
        row_index += max_lengths_dict["tracking_pre"] + 1
        data_matrix[0][row_index + 1] = "tracking POST"
        data_matrix[id_index][
        row_index + 1:row_index + 1 + len(value["continuous tracking data"]["post-imri tracking"])] \
            = value["continuous tracking data"]["post-imri tracking"]
        row_index += max_lengths_dict["tracking_post"] + 1

        data_matrix[0][row_index + 1] = "segmentations fMRI"
        data_matrix[id_index][row_index + 1:row_index + 1 + len(value["segmentations"]["pre-op fmri segmentations"])] \
            = value["segmentations"]["pre-op fmri segmentations"]
        row_index += max_lengths_dict["seg_fmir"] + 1
        data_matrix[0][row_index + 1] = "segmentations DTI"
        data_matrix[id_index][row_index + 1:row_index + 1 + len(
            value["segmentations"]["pre-op brainlab manual dti tractography segmentations"])] \
            = value["segmentations"]["pre-op brainlab manual dti tractography segmentations"]
        row_index += max_lengths_dict["seg_dti"] + 1
        data_matrix[0][row_index + 1] = "segmentations REST"
        data_matrix[id_index][row_index + 1:row_index + 1 + len(value["segmentations"]["rest"])] \
            = value["segmentations"]["rest"]
        row_index += max_lengths_dict["seg_rest"] + 1

        id_index += 1
        row_index = 2

    return data_matrix


def format_data_matrix_to_excel(data_matrix, max_lengths_dict, save_path):
    """
    Takes in the data_matrix and formats it
    :param data_matrix: The matrix to be formatted and saved
    :param max_lengths_dict: The dict containing the max lengths of the data arrays
    :param save_path: Path where the data will be saved
    :return writer: The writer which can be used to save the data
    """

    df = pd.DataFrame(data=data_matrix)
    df = (df.T)

    writer = pd.ExcelWriter(save_path, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1', index=False, header=False)
    worksheet = writer.sheets['Sheet1']
    workbook = writer.book
    merge_format = workbook.add_format({'align': 'center', 'valign': 'vcenter'})  # , 'border': 2})

    index = 0
    names = ["pre-op imaging", "intra-op US", "intra-op REST", "tracking PRE", "tracking POST", "segmentations fMRI",
             "segmentations DTI", "segmentations REST"]
    range_start = 0

    for key, value in max_lengths_dict.items():
        worksheet.merge_range(range_start + 3, 0, range_start + value + 2, 0, names[index], merge_format)

        range_start += value + 1
        index += 1

    return writer
