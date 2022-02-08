import os
import argparse

from Resources.Logic.xlsx_exporting_logic import SummarySpreadsheetSaver


def main(params):

    # create paths
    save_directory_path = params.save_directory_path
    full_dict_path = params.summary_dict_path
    spreadsheet_save_path = params.spreadsheet_path

    # create save object
    summary_saver = SummarySpreadsheetSaver(save_directory_path=save_directory_path,
                                            full_dict_path=full_dict_path,
                                            spreadsheet_save_path=spreadsheet_save_path)

    summary_saver.save()


if __name__ == "__main__":
    __package__ = "Resources.Logic"

    parser = argparse.ArgumentParser()

    parser.add_argument("-sdp", "--save_directory_path", type=str, help="Path to the save directory",
                        default="/Users/fryderykkogl/Documents/university/master/thesis/code/patient_hierarchy.nosync"
                                "/patient_summary")
    parser.add_argument("-sdp", "--summary_dict_path", type=str, help="Path to the summary dict file",
                        default="/Users/fryderykkogl/Documents/university/master/thesis/code/patient_hierarchy.nosync"
                                "/patient_summary/full_summary.json")
    parser.add_argument("-sdp", "--spreadsheet_path", type=str, help="Path to the spreadsheet save file",
                        default="/Users/fryderykkogl/Documents/university/master/thesis/code/patient_hierarchy.nosync"
                                "/patient_summary/full_summary.xlsx")
    parser.add_argument()

    arguments = parser.parse_args()

    main(arguments)
