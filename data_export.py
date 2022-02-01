import json
import pandas as pd
import argparse
import xlsxwriter



def main(params):
    # load full dict
    full_dict_path = params.summary_file
    full_data = None

    with open(full_dict_path, 'r') as f:
        # replace '%' with ' '
        text = f.read()
        text = text.replace('%', ' ')

    with open(full_dict_path, 'w+') as f:
        f.truncate(0)
        f.write(text)

    with open(full_dict_path, 'r') as f:
        full_data = json.load(f)

    if full_data is None:
        raise ValueError("Loaded dict is empty")

    # get max lengths
    lengths = {"pre_op_im": 0, "intra_us": 0, "intra_rest": 0, "tracking_pre": 0, "tracking_post": 0, "seg_fmir": 0,
               "seg_dti": 0, "seg_rest": 0}

    for key, item in full_data.items():
        # data_matrix[0].append(key)
        if len(item["pre-op imaging"]) > lengths["pre_op_im"]:
            lengths["pre_op_im"] = len(item["pre-op imaging"])
        if len(item["intra-op imaging"]["ultrasounds"]) > lengths["intra_us"]:
            lengths["intra_us"] = len(item["intra-op imaging"]["ultrasounds"])
        if len(item["intra-op imaging"]["rest"]) > lengths["intra_rest"]:
            lengths["intra_rest"] = len(item["intra-op imaging"]["rest"])
        if len(item["continuous tracking data"]["pre-imri tracking"]) > lengths["tracking_pre"]:
            lengths["tracking_pre"] = len(item["continuous tracking data"]["pre-imri tracking"])
        if len(item["continuous tracking data"]["post-imri tracking"]) > lengths["tracking_post"]:
            lengths["tracking_post"] = len(item["continuous tracking data"]["post-imri tracking"])
        if len(item["segmentations"]["pre-op fmri segmentations"]) > lengths["seg_fmir"]:
            lengths["seg_fmir"] = len(item["segmentations"]["pre-op fmri segmentations"])
        if len(item["segmentations"]["pre-op brainlab manual dti tractography segmentations"]) > lengths["seg_dti"]:
            lengths["seg_dti"] = len(item["segmentations"]["pre-op brainlab manual dti tractography segmentations"])
        if len(item["segmentations"]["rest"]) > lengths["seg_rest"]:
            lengths["seg_rest"] = len(item["segmentations"]["rest"])

    data_matrix = []

    for i in range(len(full_data) + 2):  # '+2' for volume type and empty column
        data_matrix.append([])
        for j in range(sum(lengths.values()) + 10):  # '+1' for titles and paths
            if i == len(full_data) + 1:
                data_matrix[i].append(' ')
            else:
                data_matrix[i].append('')

    id_index = 1
    row_index = 2

    for key, value in full_data.items():
        data_matrix[id_index][row_index - 2] = key
        data_matrix[id_index][row_index - 1] = value["path"]

        data_matrix[0][row_index + 1] = "pre-op imaging"
        data_matrix[id_index][row_index+1:row_index+1+len(value["pre-op imaging"])] = value["pre-op imaging"]
        row_index += lengths["pre_op_im"] + 1

        data_matrix[0][row_index + 1] = "intra-op US"
        data_matrix[id_index][row_index + 1:row_index + 1 + len(value["intra-op imaging"]["ultrasounds"])] = \
            value["intra-op imaging"]["ultrasounds"]
        row_index += lengths["intra_us"] + 1
        data_matrix[0][row_index + 1] = "intra-op REST"
        data_matrix[id_index][row_index + 1:row_index + 1 + len(value["intra-op imaging"]["rest"])] = \
            value["intra-op imaging"]["rest"]
        row_index += lengths["intra_rest"] + 1

        data_matrix[0][row_index + 1] = "tracking PRE"
        data_matrix[id_index][row_index + 1:row_index + 1 + len(value["continuous tracking data"]["pre-imri tracking"])]\
            = value["continuous tracking data"]["pre-imri tracking"]
        row_index += lengths["tracking_pre"] + 1
        data_matrix[0][row_index + 1] = "tracking POST"
        data_matrix[id_index][row_index + 1:row_index + 1 + len(value["continuous tracking data"]["post-imri tracking"])] \
            = value["continuous tracking data"]["post-imri tracking"]
        row_index += lengths["tracking_post"] + 1

        data_matrix[0][row_index + 1] = "segmentations fMRI"
        data_matrix[id_index][row_index + 1:row_index + 1 + len(value["segmentations"]["pre-op fmri segmentations"])] \
            = value["segmentations"]["pre-op fmri segmentations"]
        row_index += lengths["seg_fmir"] + 1
        data_matrix[0][row_index + 1] = "segmentations DTI"
        data_matrix[id_index][row_index + 1:row_index + 1 + len(value["segmentations"]["pre-op brainlab manual dti tractography segmentations"])] \
            = value["segmentations"]["pre-op brainlab manual dti tractography segmentations"]
        row_index += lengths["seg_dti"] + 1
        data_matrix[0][row_index + 1] = "segmentations REST"
        data_matrix[id_index][row_index + 1:row_index + 1 + len(value["segmentations"]["rest"])] \
            = value["segmentations"]["rest"]
        row_index += lengths["seg_rest"] + 1

        id_index += 1
        row_index = 2

    df = pd.DataFrame(data=data_matrix)
    df = (df.T)

    writer = pd.ExcelWriter("/Users/fryderykkogl/Documents/university/master/thesis/code/patient_hierarchy.nosync/"
                            "patient_summary/full_summary.xlsx", engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1', index=False, header=False)
    worksheet = writer.sheets['Sheet1']
    workbook = writer.book
    merge_format = workbook.add_format({'align': 'center', 'valign': 'vcenter'})  # , 'border': 2})

    index = 0
    names = ["pre-op imaging", "intra-op US", "intra-op REST", "tracking PRE", "tracking POST", "segmentations fMRI",
             "segmentations DTI", "segmentations REST"]
    range_start = 0

    for key, value in lengths.items():
        worksheet.merge_range(range_start + 3, 0, range_start + value + 2, 0, names[index], merge_format)

        range_start += value + 1
        index += 1

    writer.save()




if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("-sf", "--summary_file", type=str, help="Path to the file with all the summary dataconverted to "
                                                                ".fcsv")

    arguments = parser.parse_args()

    main(arguments)
