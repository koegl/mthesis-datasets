import os
import json

try:
    import pandas as pd
except:
    slicer.util.pip_install('library_name')
    slicer.util.pip_install('Jinja2')
    import pandas as pd


class SummarySpreadsheetSaver:
    def __init__(self, save_directory_path, full_dict_path, spreadsheet_save_path):
        self.save_directory_path = save_directory_path
        self.full_dict_path = full_dict_path
        self.spreadsheet_save_path = spreadsheet_save_path
        self.full_data_dict = None
        self.max_lengths = {"pre_op_im": 0, "intra_us": 0, "intra_rest": 0, "tracking_pre": 0, "tracking_post": 0,
                            "seg_fmir": 0, "seg_dti": 0, "seg_rest": 0}
        self.data_matrix = None
        self.writer = None

    @staticmethod
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

    def __get_max_lengths_of_data_arrays(self):
        """
        Takes a patient summary dict and fills a dict with the max max_lengths for each data array
        :param data_dict: The summary dict
        """

        for key, item in self.full_data_dict.items():
            if len(item["pre-op imaging"]) > self.max_lengths["pre_op_im"]:
                self.max_lengths["pre_op_im"] = len(item["pre-op imaging"])
            if len(item["intra-op imaging"]["ultrasounds"]) > self.max_lengths["intra_us"]:
                self.max_lengths["intra_us"] = len(item["intra-op imaging"]["ultrasounds"])
            if len(item["intra-op imaging"]["rest"]) > self.max_lengths["intra_rest"]:
                self.max_lengths["intra_rest"] = len(item["intra-op imaging"]["rest"])
            if len(item["continuous tracking data"]["pre-imri tracking"]) > self.max_lengths["tracking_pre"]:
                self.max_lengths["tracking_pre"] = len(item["continuous tracking data"]["pre-imri tracking"])
            if len(item["continuous tracking data"]["post-imri tracking"]) > self.max_lengths["tracking_post"]:
                self.max_lengths["tracking_post"] = len(item["continuous tracking data"]["post-imri tracking"])
            if len(item["segmentations"]["pre-op fmri segmentations"]) > self.max_lengths["seg_fmir"]:
                self.max_lengths["seg_fmir"] = len(item["segmentations"]["pre-op fmri segmentations"])
            if len(item["segmentations"]["pre-op brainlab manual dti tractography segmentations"]) > self.max_lengths[
                "seg_dti"]:
                self.max_lengths["seg_dti"] = len(
                    item["segmentations"]["pre-op brainlab manual dti tractography segmentations"])
            if len(item["segmentations"]["rest"]) > self.max_lengths["seg_rest"]:
                self.max_lengths["seg_rest"] = len(item["segmentations"]["rest"])

    def __create_empty_data_matrix(self):
        """
        Create an empty data matrix that will be written to an excel spreadsheet
        :param data_summary_length: Amount of different patients
        :param max_array_lengths_sum: The sum of all the maximal lengths of the data arrays
        :return:
        """

        data_summary_length = len(self.full_data_dict) + 2  # '+ 2' for volume type and empty column at the back to stop
        # spill
        max_array_lengths_sum = sum(self.max_lengths.values()) + 10  # '+ 10' for titles, paths and empty rows

        empty_data_matrix = []

        for i in range(data_summary_length):  # '+2' for volume type and empty column
            empty_data_matrix.append([])
            for j in range(max_array_lengths_sum + 10):  # '+1' for titles and paths
                empty_data_matrix[i].append(' ')

        return empty_data_matrix

    def __create_matrix_from_summary_dict(self):
        """
        Create a data matrix with all the values from the summary dict
        :return: The filled data_matrix
        """

        # get max max_lengths
        self.__get_max_lengths_of_data_arrays()

        self.data_matrix = self.__create_empty_data_matrix()

        id_index = 1
        row_index = 2

        # set 'path' and 'id' values
        self.data_matrix[0][0] = 'ID'
        self.data_matrix[0][1] = 'file path'

        for key, value in self.full_data_dict.items():
            self.data_matrix[id_index][row_index - 2] = key
            self.data_matrix[id_index][row_index - 1] = value["path"][0]

            self.data_matrix[0][row_index + 1] = "pre-op imaging"
            self.data_matrix[id_index][row_index + 1:row_index + 1 + len(value["pre-op imaging"])] = value["pre-op imaging"]
            row_index += self.max_lengths["pre_op_im"] + 1

            self.data_matrix[0][row_index + 1] = "intra-op US"
            self.data_matrix[id_index][row_index + 1:row_index + 1 + len(value["intra-op imaging"]["ultrasounds"])] = \
                value["intra-op imaging"]["ultrasounds"]
            row_index += self.max_lengths["intra_us"] + 1
            self.data_matrix[0][row_index + 1] = "intra-op REST"
            self.data_matrix[id_index][row_index + 1:row_index + 1 + len(value["intra-op imaging"]["rest"])] = \
                value["intra-op imaging"]["rest"]
            row_index += self.max_lengths["intra_rest"] + 1

            self.data_matrix[0][row_index + 1] = "tracking PRE"
            self.data_matrix[id_index][
            row_index + 1:row_index + 1 + len(value["continuous tracking data"]["pre-imri tracking"])] \
                = value["continuous tracking data"]["pre-imri tracking"]
            row_index += self.max_lengths["tracking_pre"] + 1
            self.data_matrix[0][row_index + 1] = "tracking POST"
            self.data_matrix[id_index][
            row_index + 1:row_index + 1 + len(value["continuous tracking data"]["post-imri tracking"])] \
                = value["continuous tracking data"]["post-imri tracking"]
            row_index += self.max_lengths["tracking_post"] + 1

            self.data_matrix[0][row_index + 1] = "segmentations fMRI"
            self.data_matrix[id_index][
            row_index + 1:row_index + 1 + len(value["segmentations"]["pre-op fmri segmentations"])] \
                = value["segmentations"]["pre-op fmri segmentations"]
            row_index += self.max_lengths["seg_fmir"] + 1
            self.data_matrix[0][row_index + 1] = "segmentations DTI"
            self.data_matrix[id_index][row_index + 1:row_index + 1 + len(
                value["segmentations"]["pre-op brainlab manual dti tractography segmentations"])] \
                = value["segmentations"]["pre-op brainlab manual dti tractography segmentations"]
            row_index += self.max_lengths["seg_dti"] + 1
            self.data_matrix[0][row_index + 1] = "segmentations REST"
            self.data_matrix[id_index][row_index + 1:row_index + 1 + len(value["segmentations"]["rest"])] \
                = value["segmentations"]["rest"]
            row_index += self.max_lengths["seg_rest"] + 1

            id_index += 1
            row_index = 2

    def __format_data_matrix_to_excel(self):
        """
        Formats the data_matrix and formats it
        """
        # todo implement this as own functin to remove borders:
        # https://xlsxwriter.readthedocs.io/working_with_pandas.html#formatting-of-the-dataframe-headers

        df = pd.DataFrame(data=self.data_matrix)
        df = (df.T)

        self.writer = pd.ExcelWriter(self.spreadsheet_save_path, engine='xlsxwriter')
        df.to_excel(self.writer, sheet_name='Sheet1', index=False, header=False)
        worksheet = self.writer.sheets['Sheet1']
        workbook = self.writer.book
        merge_format = workbook.add_format({'align': 'center', 'valign': 'vcenter'})  # , 'border': 2})

        index = 0
        names = ["pre-op imaging", "intra-op US", "intra-op REST", "tracking PRE", "tracking POST",
                 "segmentations fMRI",
                 "segmentations DTI", "segmentations REST"]
        range_start = 0

        # make first row bold
        bold_font = workbook.add_format({'bold': True})
        worksheet.set_row(0, None, bold_font)

        # merge
        for key, value in self.max_lengths.items():
            worksheet.merge_range(range_start + 3, 0, range_start + value + 2, 0, names[index], merge_format)

            range_start += value + 1
            index += 1

    def save(self):

        # preprocess summary file - replace '%' with ' ' in summary file
        self.replace_character_in_file(self.full_dict_path, '%', ' ')

        # load full summary dict
        with open(self.full_dict_path, 'r') as f:
            self.full_data_dict = json.load(f)

        if self.full_data_dict is None:
            raise ValueError("Loaded dict is empty")

        # create data matrix with values from the summary dict
        self.__create_matrix_from_summary_dict()

        # format the data_matrix to a spreadsheet
        self.__format_data_matrix_to_excel()

        # save the spreadsheet
        self.writer.save()
