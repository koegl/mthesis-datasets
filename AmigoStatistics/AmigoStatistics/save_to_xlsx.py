import os
import argparse

from Resources.Logic.xlsx_exporting_logic import SummarySpreadsheetSaver


def main():

    # create paths
    save_directory_path = "/Users/fryderykkogl/Documents/university/master/thesis/code/patient_hierarchy.nosync" \
                          "/patient_summary"
    full_dict_path = "/Users/fryderykkogl/Documents/university/master/thesis/code/patient_hierarchy.nosync" \
                     "/patient_summary/full_summary.json"
    spreadsheet_save_path = "/Users/fryderykkogl/Documents/university/master/thesis/code/patient_hierarchy.nosync" \
                            "/patient_summary/full_summary.xlsx"

    # create save object
    summary_saver = SummarySpreadsheetSaver(save_directory_path=save_directory_path,
                                            full_dict_path=full_dict_path,
                                            spreadsheet_save_path=spreadsheet_save_path)

    summary_saver.save()


if __name__ == "__main__":

    main()
