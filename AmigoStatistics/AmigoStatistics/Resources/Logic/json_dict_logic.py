import json
import os
from os.path import exists
import vtk
import slicer


class SinglePatientDictLogic:

    def __init__(self):
        self.all_fake_paths = []

    @staticmethod
    def create_empty_dict_entry(mrm, path):
        """
        Add an empty dict entry
        """

        dictionary = {mrm: {
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
        }}

        return dictionary

    def get_fake_paths_of_all_nodes(self, sh_folder_item_id, output_folder=""):

        # Get items in the folder
        childIds = vtk.vtkIdList()
        shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
        shNode.GetItemChildren(sh_folder_item_id, childIds)
        if childIds.GetNumberOfIds() == 0:
            return

        # Write each child item to file
        for itemIdIndex in range(childIds.GetNumberOfIds()):
            shItemId = childIds.GetId(itemIdIndex)

            # Write node to file (if storable)
            dataNode = shNode.GetItemDataNode(shItemId)
            if dataNode and dataNode.IsA("vtkMRMLStorableNode") and dataNode.GetStorageNode():
                storageNode = dataNode.GetStorageNode()
                filename = os.path.basename(storageNode.GetFileName())
                filepath = output_folder + "/" + filename

                self.all_fake_paths.append(filepath)

            # Write all children of this child item
            grandChildIds = vtk.vtkIdList()
            shNode.GetItemChildren(shItemId, grandChildIds)
            if grandChildIds.GetNumberOfIds() > 0:
                self.get_fake_paths_of_all_nodes(shItemId, output_folder + "/" + shNode.GetItemName(shItemId))

    def populate_dict_with_hierarchy_new(self, patient_id, patient_path):
        """
        Takes the 'paths' generated by get_fake_paths_of_all_nodes and assigns them to the correct place in the summary
        dictionary
        :param: patient_id: Id of the patient
        :param: patient_path: Path to the patient .mrb
        :return: The populated summary dict
        """

        # get all the paths to the nodes
        shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
        slicer.app.ioManager().addDefaultStorageNodes()
        self.get_fake_paths_of_all_nodes(shNode.GetSceneItemID())

        self.single_patients_dict = self.create_empty_dict_entry(patient_id, patient_path)

        # populate the dict
        for path in self.all_fake_paths:

            # extract node name (get last term in path and then remove the extension)
            node_name = path.split('/')[-1].split('.')[0]

            if all(x in path.lower() for x in ["pre", "op", "imaging"]) \
                    and not any(x in path.lower() for x in ["ultrasound", "intra-op", "contin", "tracking", "segmentati"]):
                self.single_patients_dict[patient_id]["pre-op imaging"].append(node_name)

            elif all(x in path.lower() for x in ["intra", "op", "imagi", "ultrasound"]) \
                    and not any(x in path.lower() for x in ["pre-op", "contin", "tracking", "segmentati"]):
                self.single_patients_dict[patient_id]["intra-op imaging"]["ultrasounds"].append(node_name)
            elif all(x in path.lower() for x in ["intra", "op", "imaging"]) \
                    and not any(x in path.lower() for x in ["pre-op", "contin", "tracking", "segmentati"]):
                self.single_patients_dict[patient_id]["intra-op imaging"]["rest"].append(node_name)

            elif all(x in path.lower() for x in ["contin", "tracking", "post"]) \
                    and not any(x in path.lower() for x in ["segmentati", "imaging"]):
                self.single_patients_dict[patient_id]["continuous tracking data"]["post-imri tracking"].append(node_name)
            elif all(x in path.lower() for x in ["contin", "tracking", "pre"]) \
                    and not any(x in path.lower() for x in ["segmentati", "imaging"]):
                self.single_patients_dict[patient_id]["continuous tracking data"]["pre-imri tracking"].append(node_name)

            elif all(x in path.lower() for x in ["segmentation", "pre-op", "fmri"]) \
                    and not any(x in path.lower() for x in ["contin", "tracking", "imaging"]):
                self.single_patients_dict[patient_id]["segmentations"]["pre-op fmri segmentations"].append(node_name)
            elif all(x in path.lower() for x in ["segmentation", "brainlab", "dti"]) \
                    and not any(x in path.lower() for x in ["contin", "tracking", "imaging"]):
                self.single_patients_dict[patient_id]["segmentations"]["pre-op brainlab manual dti tractography " \
                                                                       "segmentations"].append(node_name)
            elif all(x in path.lower() for x in ["segmentation"]) \
                    and not any(x in path.lower() for x in ["contin", "tracking", "imaging"]):
                self.single_patients_dict[patient_id]["segmentations"]["rest"].append(node_name)

    def dump_hierarchy_to_json(self, patient_id, data_json_path, scene_path):
        """
        Dumps entire hierarchy to a json
        """

        if exists(data_json_path):
            data_json_path = data_json_path[:-5]

            for i in range(2, 100):  # create a new path with an index at the end
                if not exists("{}_{}.json".format(data_json_path, i)):
                    data_json_path = "{}_{}.json".format(data_json_path, i)
                    break

        self.populate_dict_with_hierarchy_new(patient_id, scene_path)

        f = open(data_json_path, "w")
        json.dump(self.single_patients_dict, f)
        f.close()

        # clear all previous paths
        self.all_fake_paths = []


class SummaryPatientDictLogic:
    def __init__(self):
        self.all_fake_paths = []
        self.data_missing = {}
        self.single_patients_dict = {}

    @staticmethod
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

        # save full dict
        full_summary_file = open(save_path, 'w')
        json.dump(full_summary_dict, full_summary_file)
        full_summary_file.close()

    def check_dictionary_for_completeness(self, data_dict):
        """
        Check if each array in the dict is populated, if not write some kind of error log. Works on a full completeness dict
        """

        for key, item in data_dict.items():
            self.data_missing[key] = [item["path"]]

            if len(item["pre-op imaging"]) == 0:
                self.data_missing[key].append("pre-op imaging")

            if len(item["intra-op imaging"]["ultrasounds"]) == 0:
                self.data_missing[key].append("intra-op imaging - ultrasounds")
            if len(item["intra-op imaging"]["rest"]) == 0:
                self.data_missing[key].append("intra-op imaging - rest")

            if len(item["continuous tracking data"]["pre-imri tracking"]) == 0:
                self.data_missing[key].append("continuous tracking data - pre-imri tracking")
            if len(item["continuous tracking data"]["post-imri tracking"]) == 0:
                self.data_missing[key].append("continuous tracking data - post-imri tracking")

            if len(item["segmentations"]["pre-op fmri segmentations"]) == 0:
                self.data_missing[key].append("segmentations - pre-op fmri segmentations")
            if len(item["segmentations"]["pre-op brainlab manual dti tractography segmentations"]) == 0:
                self.data_missing[key].append("segmentations - pre-op brainlab manual dti tractography segmentations")
            if len(item["segmentations"]["rest"]) == 0:
                self.data_missing[key].append("segmentations - rest")

            if len(self.data_missing[
                       key]) == 1:  # if nothing missing was found, remove the entry (1 means we only added the path)
                del self.data_missing[key]

    def dump_full_completenes_dict_to_json(self, full_summary_path, save_path):
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
        self.check_dictionary_for_completeness(full_summary)

        # save completeness dict
        completeness_file = open(save_path, "w+")
        completeness_file.truncate(0)
        json.dump(self.data_missing, completeness_file)
        completeness_file.close()

        for key, item in self.data_missing.items():
            print("\nCase {}({}) misses the following data:\n{}\n".format(key, item[0], item[1:]))
