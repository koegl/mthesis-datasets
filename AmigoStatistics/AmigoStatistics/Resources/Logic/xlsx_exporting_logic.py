import os
import json
from operator import itemgetter

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

        # load frontiers ids and convert to ints
        with open("/Users/fryderykkogl/Documents/university/master/thesis/code/patient_hierarchy.nosync/frontiers_ids"
                  ".json") as frontiers_ids_file:
            frontiers_dict = json.load(frontiers_ids_file)
            self.frontiers_ids = frontiers_dict["ids"]

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

    @staticmethod
    def __remove_list_element_by_content(pop_list: list, content: str) -> list:
        """
        Removes all lists elements that contain 'content'. Returns list and amount of elements removed.
        Matches exactly, not by all lower case
        :return: List and success bool
        """

        # a copy is needed, otherwise popping on a running list results in problesm
        return_list = pop_list.copy()

        for element in pop_list:
            if content in element:
                return_list.remove(element)

        # if it didn't find anything
        return return_list

    @staticmethod
    def __remove_list_element_by_content_invert(pop_list: list, content: str) -> list:
        """
        Removes all lists elements that do not contain 'content'. Returns list and amount of elements removed.
        Matches exactly, not by all lower case
        :return: List and success bool
        """

        # a copy is needed, otherwise popping on a running list results in problesm
        return_list = pop_list.copy()

        for element in pop_list:
            if content not in element:
                return_list.remove(element)

        # if it didn't find anything
        return return_list

    def __fine_tune__summary_dict(self):
        """
        Additional fien tuning of the summary dict
        :return:
        """
        for key, value in self.full_data_dict.items():
            # remove volumes in pre-op imaging that do not contain '3D'
            # self.full_data_dict[key]["pre-op imaging"] = \
            #     self.__remove_list_element_by_content_invert(self.full_data_dict[key]["pre-op imaging"], "3D")

            # remove volumes in pre-op imaging that contain 'CT'
            self.full_data_dict[key]["pre-op imaging"] = \
                self.__remove_list_element_by_content(self.full_data_dict[key]["pre-op imaging"], "CT")

            # remove volumes in intra-op imaging rest that do not contain '3D'
            # self.full_data_dict[key]["intra-op imaging"]["rest"] = \
            #   self.__remove_list_element_by_content_invert(self.full_data_dict[key]["intra-op imaging"]["rest"], "3D")

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

        data_summary_length = len(
            self.full_data_dict)  # + 2  # '+ 2' for volume type and empty column at the back to stop
        # spill
        max_array_lengths_sum = sum(self.max_lengths.values()) + 10  # '+ 10' for path, frontiers and empty rows

        empty_data_matrix = []

        for i in range(data_summary_length):
            empty_data_matrix.append([])
            for j in range(max_array_lengths_sum):
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

        id_index = 0
        row_index = 2

        self.column_headers = [[], []]

        for key, value in self.full_data_dict.items():
            self.column_headers[0].append(key)
            self.column_headers[1].append(value["path"][0])

            # add frontiers mark (if the case was in frontiers)
            if key in self.frontiers_ids:
                self.data_matrix[id_index][row_index - 2] = "FRONTIERS"

            # add path
            self.data_matrix[id_index][row_index - 1] = value["path"][0]

            # self.data_matrix[0][row_index + 1] = "pre-op imaging"
            self.data_matrix[id_index][row_index + 1:row_index + 1 + len(value["pre-op imaging"])] = value["pre-op " \
                                                                                                           "imaging"]
            row_index += self.max_lengths["pre_op_im"] + 1

            # self.data_matrix[0][row_index + 1] = "intra-op US"
            self.data_matrix[id_index][row_index + 1:row_index + 1 + len(value["intra-op imaging"]["ultrasounds"])] = \
                value["intra-op imaging"]["ultrasounds"]
            row_index += self.max_lengths["intra_us"] + 1
            # self.data_matrix[0][row_index + 1] = "intra-op REST"
            self.data_matrix[id_index][row_index + 1:row_index + 1 + len(value["intra-op imaging"]["rest"])] = \
                value["intra-op imaging"]["rest"]
            row_index += self.max_lengths["intra_rest"] + 1

            # self.data_matrix[0][row_index + 1] = "tracking PRE"
            self.data_matrix[id_index][
            row_index + 1:row_index + 1 + len(value["continuous tracking data"]["pre-imri tracking"])] \
                = value["continuous tracking data"]["pre-imri tracking"]
            row_index += self.max_lengths["tracking_pre"] + 1
            # self.data_matrix[0][row_index + 1] = "tracking POST"
            self.data_matrix[id_index][
            row_index + 1:row_index + 1 + len(value["continuous tracking data"]["post-imri tracking"])] \
                = value["continuous tracking data"]["post-imri tracking"]
            row_index += self.max_lengths["tracking_post"] + 1

            # self.data_matrix[0][row_index + 1] = "segmentations fMRI"
            self.data_matrix[id_index][
            row_index + 1:row_index + 1 + len(value["segmentations"]["pre-op fmri segmentations"])] \
                = value["segmentations"]["pre-op fmri segmentations"]
            row_index += self.max_lengths["seg_fmir"] + 1
            # self.data_matrix[0][row_index + 1] = "segmentations DTI"
            self.data_matrix[id_index][row_index + 1:row_index + 1 + len(
                value["segmentations"]["pre-op brainlab manual dti tractography segmentations"])] \
                = value["segmentations"]["pre-op brainlab manual dti tractography segmentations"]
            row_index += self.max_lengths["seg_dti"] + 1
            # self.data_matrix[0][row_index + 1] = "segmentations REST"
            self.data_matrix[id_index][row_index + 1:row_index + 1 + len(value["segmentations"]["rest"])] \
                = value["segmentations"]["rest"]
            row_index += self.max_lengths["seg_rest"] + 1

            id_index += 1
            row_index = 2

        print(self.column_headers)

    def __sort_data_matrix(self):
        """
        Sorts the data matrix according to the dates (paths)
        """
        self.data_matrix = sorted(self.data_matrix, key=itemgetter(1))

        # the headers list has to be sorted because for assigning warning colours we access the full dict - so we need
        # the sorted keys
        # transpose the headers list
        headers_transpose = []
        for key, path in zip(self.column_headers[0], self.column_headers[1]):
            headers_transpose.append([key, path])

        # sort the headers list
        headers_transpose = sorted(headers_transpose, key=itemgetter(1))

        # transpose the transposed
        self.column_headers = [[], []]
        for key, path in headers_transpose:
            self.column_headers[0].append(key)
            self.column_headers[1].append(path)

    @staticmethod
    def __list_contains(check_list: list, content: str) -> bool:
        """
        Check if anywere in the list the content is present. Case in-sensitive.
        :param check_list: List to check for content
        :param content: Content
        :return: True if content is in list, else False
        """

        for element in check_list:
            if content.lower() in element.lower():
                return True

        # base case (nothing found)
        return False

    def __assign_warning_colours(self):
        """
        Assign colours to cells to warn the user
        """

        # https://xlsxwriter.readthedocs.io/working_with_conditional_formats.html
        format_orange = self.workbook.add_format({'bg_color': '#FFA500'})

        header_index = 1
        col_init = 4
        path_row = 2
        # https://cxn03651.github.io/write_xlsx/conditional_formatting.html
        # dict is not sorted, so we have to use the sorted headers
        for key in self.column_headers[0]:
            value = self.full_data_dict[key]
            # for key, value in self.full_data_dict.items():

            # check if they contain T1 and T2
            if not (self.__list_contains(value["pre-op imaging"], 't2')
                    and self.__list_contains(value["pre-op imaging"], 't1')):
                # first_row, first_col, last_row, last_col
                self.worksheet.conditional_format(path_row, header_index, path_row, header_index, {'type': 'cell',
                                                                                     'criteria': '>=',
                                                                                     'value': -999999999,
                                                                                     'format': format_orange})

                col_start = col_init
                col_end = col_start + self.max_lengths["pre_op_im"] - 1
                self.worksheet.conditional_format(col_start, header_index, col_end, header_index,
                                                  {'type': 'cell',
                                                   'criteria': '>=',
                                                   'value': -999999999,
                                                   'format': format_orange})

            # check if there are less than two US images
            if len(value["intra-op imaging"]["ultrasounds"]) <= 2:
                self.worksheet.conditional_format(path_row, header_index, path_row, header_index, {'type': 'cell',
                                                                                     'criteria': '>=',
                                                                                     'value': -999999999,
                                                                                     'format': format_orange})
                col_start = col_init + self.max_lengths["pre_op_im"] - 1 + 2
                col_end = col_start + self.max_lengths["intra_us"] - 1
                self.worksheet.conditional_format(col_start, header_index, col_end, header_index,
                                                  {'type': 'cell',
                                                   'criteria': '>=',
                                                   'value': -999999999,
                                                   'format': format_orange})

            # check if there are more than 0 intra-op MRs
            if len(value["intra-op imaging"]["rest"]) == 0:
                self.worksheet.conditional_format(path_row, header_index, path_row, header_index, {'type': 'cell',
                                                                                     'criteria': '>=',
                                                                                     'value': -999999999,
                                                                                     'format': format_orange})
                col_start = col_init + self.max_lengths["pre_op_im"] + self.max_lengths["intra_us"] - 1 + 2 + 1
                col_end = col_start + self.max_lengths["intra_rest"] - 1
                self.worksheet.conditional_format(col_start, header_index, col_end, header_index,
                                                  {'type': 'cell',
                                                   'criteria': '>=',
                                                   'value': -999999999,
                                                   'format': format_orange})

            header_index += 1

    def __format_data_matrix_to_excel(self):
        """
        Formats the data_matrix and formats it
        """
        # todo implement this as own functin to remove borders:
        # https://xlsxwriter.readthedocs.io/working_with_pandas.html#formatting-of-the-dataframe-headers

        row_names = [' ' for x in range(sum(self.max_lengths.values()) + 10)]
        row_names[1] = "path"
        df = pd.DataFrame(data=self.data_matrix, index=self.column_headers[0], columns=row_names)
        df = (df.T)

        self.writer = pd.ExcelWriter(self.spreadsheet_save_path, engine='xlsxwriter')
        df.to_excel(self.writer, sheet_name='Sheet1')
        self.worksheet = self.writer.sheets['Sheet1']
        self.workbook = self.writer.book

        index = 0
        names = ["pre-op imaging", "intra-op US", "intra-op MR", "tracking PRE", "tracking POST",
                 "segmentations fMRI",
                 "segmentations DTI", "segmentations REST"]
        range_start = 0

        # make first row bold
        bold_font = self.workbook.add_format({'bold': True})
        self.worksheet.set_row(0, None, bold_font)

        # merge
        merge_format = self.workbook.add_format({'align': 'center', 'valign': 'vcenter'})  # , 'border': 2})

        for key, value in self.max_lengths.items():
            self.worksheet.merge_range(range_start + 3, 0, range_start + value + 2, 0, names[index], merge_format)

            range_start += value + 1
            index += 1

        # colours
        self.__assign_warning_colours()

    def save(self):

        # preprocess summary file - replace '%' with ' ' in summary file
        self.replace_character_in_file(self.full_dict_path, '%', ' ')

        # load full summary dict
        with open(self.full_dict_path, 'r') as f:
            self.full_data_dict = json.load(f)

        # remove some additional elements from the summary dict
        self.__fine_tune__summary_dict()

        if self.full_data_dict is None:
            raise ValueError("Loaded dict is empty")

        # create data matrix with values from the summary dict
        self.__create_matrix_from_summary_dict()

        # sort data matrix
        self.__sort_data_matrix()

        # format the data_matrix to a spreadsheet
        self.__format_data_matrix_to_excel()

        # save the spreadsheet
        self.writer.save()
