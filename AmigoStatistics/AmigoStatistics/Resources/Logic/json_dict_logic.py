import json


def check_dictionary_for_completeness(data_dict):
    """
    Check if each array in the dict is populated, if not write some kind of error log
    """
    data_missing = {}

    for key, item in data_dict.items():
        data_missing[key] = [item["path"]]

        if len(item["pre-op imaging"]) == 0:
            data_missing[key].append("pre-op imaging")

        if len(item["intra-op imaging"]["ultrasounds"]) == 0:
            data_missing[key].append("intra-op imaging - ultrasounds")
        if len(item["intra-op imaging"]["rest"]) == 0:
            data_missing[key].append("intra-op imaging - rest")

        if len(item["continuous tracking data"]["pre-imri tracking"]) == 0:
            data_missing[key].append("continuous tracking data - pre-imri tracking")
        if len(item["continuous tracking data"]["post-imri tracking"]) == 0:
            data_missing[key].append("continuous tracking data - post-imri tracking")

        if len(item["segmentations"]["pre-op fmri segmentations"]) == 0:
            data_missing[key].append("segmentations - pre-op fmri segmentations")
        if len(item["segmentations"]["pre-op brainlab manual dti tractography segmentations"]) == 0:
            data_missing[key].append("segmentations - pre-op brainlab manual dti tractography segmentations")
        if len(item["segmentations"]["rest"]) == 0:
            data_missing[key].append("segmentations - rest")

        if len(data_missing[
                   key]) == 1:  # if nothing missing was found, remove the entry (1 means we only added the path)
            del data_missing[key]

    return data_missing

