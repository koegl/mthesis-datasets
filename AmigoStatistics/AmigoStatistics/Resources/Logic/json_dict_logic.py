import json
import os
from os.path import exists
import vtk
import slicer


def check_dictionary_for_completeness(data_dict):
    """
    Check if each array in the dict is populated, if not write some kind of error log. Works on a full completeness dict
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


def create_empty_dict_entry(dictionary, mrm, path):
    """
    Add an empty dict entry
    """

    dictionary[mrm] = {
        "path": [path],
        "pre-op imaging": [],
        "intra-op imaging": {
            "ultrasounds": [],
            "rest": []
        },
        "continuous tracking data": {
            "pre-imri tracking": [],
            "post-imri tracking": []
        },
        "segmentations": {
            "pre-op fmri segmentations": [],
            "pre-op brainlab manual dti tractography segmentations": [],
            "rest": []
        }
    }

    return dictionary


def populate_dict_with_hierarchy(sh_folder_item_id, patient_id, storage_dict, scene_path, hierarchy_ori=None):
    """
    Populate a dict entry with the hierarchy of an opened scene
    """

    hierarchy = hierarchy_ori

    if not hierarchy_ori:
        hierarchy_ori = ""

    if not hierarchy:
        hierarchy = ""
    else:
        hierarchy = hierarchy.split('/')
        del hierarchy[0]

        if any(x in hierarchy[0].lower() for x in ["patient", patient_id]):
            del hierarchy[0]  # remove first element because it's the patient case

    child_ids = vtk.vtkIdList()
    sh_node = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    sh_node.GetItemChildren(sh_folder_item_id, child_ids)
    if child_ids.GetNumberOfIds() == 0:
        return

    # Write each child item to file
    for itemIdIndex in range(child_ids.GetNumberOfIds()):
        sh_item_id = child_ids.GetId(itemIdIndex)
        # Write node to file (if storable)
        data_node = sh_node.GetItemDataNode(sh_item_id)
        if data_node and data_node.IsA("vtkMRMLStorableNode") and data_node.GetStorageNode():
            storage_node = data_node.GetStorageNode()
            filename = os.path.basename(storage_node.GetFileName())

            if patient_id not in storage_dict:
                storage_dict = create_empty_dict_entry(storage_dict, patient_id, scene_path)

            if not hierarchy:  # we are at the end
                return storage_dict

            if all(x in hierarchy[0].lower() for x in ["pre", "op", "imaging"]):
                storage_dict[patient_id]["pre-op imaging"].append(filename)

            elif all(x in hierarchy[0].lower() for x in ["intra", "op", "imaging"]):
                if len(hierarchy) == 1:
                    storage_dict[patient_id]["intra-op imaging"]["rest"].append(filename)
                else:
                    storage_dict[patient_id]["intra-op imaging"]["ultrasounds"].append(filename)

            elif all(x in hierarchy[0].lower() for x in ["contin", "tracking"]):
                if len(hierarchy) == 1:
                    if "post" in filename.lower():
                        storage_dict[patient_id]["continuous tracking data"]["post-imri tracking"].append(filename)
                    else:
                        storage_dict[patient_id]["continuous tracking data"]["pre-imri tracking"].append(filename)

                elif all(x in hierarchy[1].lower() for x in ["pre", "imri", "tracking"]):
                    storage_dict[patient_id]["continuous tracking data"]["pre-imri tracking"].append(filename)
                elif all(x in hierarchy[1].lower() for x in ["post", "imri", "tracking"]):
                    storage_dict[patient_id]["continuous tracking data"]["post-imri tracking"].append(filename)

            elif "segmentations" in hierarchy[0].lower():
                if len(hierarchy) == 1:
                    storage_dict[patient_id]["segmentations"]["rest"].append(filename)
                elif all(x in hierarchy[1].lower() for x in ["pre-op", "fmri"]):
                    storage_dict[patient_id]["segmentations"]["pre-op fmri segmentations"].append(filename)
                elif all(x in hierarchy[1].lower() for x in ["brainlab", "dti"]):
                    storage_dict[patient_id]["segmentations"][
                        "pre-op brainlab manual dti tractography segmentations"].append(filename)

        # Write all children of this child item
        grand_child_ids = vtk.vtkIdList()
        sh_node.GetItemChildren(sh_item_id, grand_child_ids)
        if grand_child_ids.GetNumberOfIds() > 0:
            populate_dict_with_hierarchy(sh_item_id, patient_id, storage_dict, scene_path,
                                         hierarchy_ori + "/" + sh_node.GetItemName(sh_item_id))

    return storage_dict


def dump_hierarchy_to_json(patient_id, data_json_path, scene_path):
    """
    Dumps entire hierarchy to a json
    """

    if exists(data_json_path):
        # check if file is empty
        if os.stat(data_json_path).st_size == 0:
            patients_dict = {}
            os.remove(data_json_path)
        else:  # if not empty, we can load it (we assume it is correct)
            load_file = open(data_json_path, "r+")
            patients_dict = json.load(load_file)
            load_file.truncate(0)  # clear file so we can store the updated dict
            load_file.close()
            os.remove(data_json_path)
    else:
        patients_dict = {}

    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    slicer.app.ioManager().addDefaultStorageNodes()

    if str(patient_id) not in patients_dict:  # it was already parsed at some point
        patients_dict = populate_dict_with_hierarchy(shNode.GetSceneItemID(), patient_id, patients_dict, scene_path)

        f = open(data_json_path, "a")
        json.dump(patients_dict, f)
        f.close()


def combine_single_summaries(summary_paths, save_path):
    """
    Combines single summaries into one big summary (and deletes the single files)
    :param summary_paths: The paths to be combined
    :param save_path: The main summary to be created
    """

    full_summary_dict = {}

    for data_summary_path in summary_paths:
        # check if dict contains something
        if not exists(data_summary_path):
            print("{} to combine could not be found".format(data_summary_path))
            continue
        if os.stat(data_summary_path).st_size == 0:
            print("No data found in the .json to combine")
            continue

        # load dict with all data
        single_sumary = open(data_summary_path, "r")
        full_summary_dict.update(json.load(single_sumary))
        single_sumary.close()

        # remove the single summary file
        os.remove(data_summary_path)

    # save full dict
    full_summary_file = open(save_path, 'w')
    json.dump(full_summary_dict, full_summary_file)
    full_summary_file.close()


def dump_full_completenes_dict_to_json(full_summary_path, save_path):
    """
    Gather all summary files and combine into one completness dict
    """

    # open file and check it
    if exists(full_summary_path):
        full_summary_dict_file = open(full_summary_path, "r")
        full_summary = json.load(full_summary_dict_file)
        full_summary_dict_file.close()
    else:
        raise ValueError("Could not read {}} - it does not exist".format(full_summary_path))
    if os.stat(full_summary_path).st_size == 0:
        raise ValueError("No data found in the .json to check for completeness")

    # populate the missing data dict
    data_missing = check_dictionary_for_completeness(full_summary)

    # save completeness dict
    completeness_file = open(save_path, "w+")
    completeness_file.truncate(0)
    json.dump(data_missing, completeness_file)
    completeness_file.close()

    for key, item in data_missing.items():
        print("\nCase {}({}) misses the following data:\n{}\n".format(key, item[0], item[1:]))
