import slicer

from AdditionalLogic.structure_logic import StructureLogic
from AdditionalLogic.tree import Tree


class StatisticsExportingLogic:
    """
    Class to encapsulate logic for exporting mrb volume statistics.
    """

    def __init__(self):
        self.current_folder_structure = None
        self.multiple_folder_structures = []

        self.preop_mr = []
        self.preop_mr_lower = []
        self.intraop_us = []
        self.intraop_us_lower = []
        self.intraop_mr = []
        self.intraop_mr_lower = []
        self.segmentations = []
        self.segmentations_lower = []

    def export_current_scene(self, export_path=None):

        # load structure tree
        self.current_folder_structure = StructureLogic.bfs_generate_folder_structure_as_tree()

        if export_path is None:  # then just print the stats
            self.current_folder_structure.print_tree()
            pass

    def combine_trees(self):
        """
        Combines multiple trees into four lists that contain the set of all scans
        @param tree_list: A list containing all the trees
        """

        for tree in self.multiple_folder_structures:
            for key, item in tree.children.items():
                for key_child, item_child in item.children.items():
                    if "pre" in key.lower() and key_child.lower() not in self.preop_mr_lower:
                        self.preop_mr.append(key_child)
                        self.preop_mr_lower.append(key_child.lower())

                    elif "intra" in key.lower() and "us" in key.lower() and key_child.lower() not in self.intraop_us_lower:
                        self.intraop_us.append(key_child)
                        self.intraop_us_lower.append(key_child.lower())

                    elif "intra" in key.lower() and "mr" in key.lower() and key_child.lower() not in self.intraop_mr_lower:
                        self.intraop_mr.append(key_child)
                        self.intraop_mr_lower.append(key_child.lower())

                    elif "segment" in key.lower() and key_child.lower() not in self.segmentations_lower:
                        self.segmentations.append(key_child)
                        self.segmentations_lower.append(key_child.lower())

        self.clean_up_combined_lists()

    def clean_up_combined_lists(self):
        self.preop_mr.sort()
        self.intraop_us.sort()
        self.intraop_mr.sort()
        self.segmentations.sort()

        all_lists = [self.preop_mr, self.intraop_us, self.intraop_mr, self.segmentations]

        for i in range(len(all_lists)):
            list = all_lists[i]

            for j in range(len(list)):
                name = list[j]

                name = name.replace("3D", "")
                name = name.replace("AX", "")
                name = name.replace("SAG", "")
                name = name.replace("NAV", "")
                name = name.replace("COR", "")
                name = name.replace("Pre-op", "")
                name = name.replace("pre-op", "")
                name = name.replace("Pre-OP", "")
                name = name.replace("Thin-cut", "")
                name = name.replace("Intra-op", "")
                name = name.replace("  ", "")
                name = name.replace("   ", "")
                name = name.replace("    ", "")
                name = name.replace("3D", "")
                name = name.replace("3D", "")
                name = name.replace("3D", "")

                list[j] = name

            all_lists[i] = list

        self.preop_mr = []
        self.preop_mr_lower = []
        self.intraop_us = []
        self.intraop_us_lower = []
        self.intraop_mr = []
        self.intraop_mr_lower = []
        self.segmentations = []
        self.segmentations_lower = []

        # create the lists again
        for i in range(len(all_lists)):
            list = all_lists[i]

            for j in range(len(list)):
                name = list[j]

                if i == 0 and name.lower() not in self.preop_mr_lower:
                    self.preop_mr.append(name)
                    self.preop_mr_lower.append(name.lower())

                elif i == 1 and name.lower() not in self.intraop_us:
                    self.intraop_us.append(name)
                    self.intraop_us_lower.append(name.lower())

                elif i == 2 and name.lower() not in self.intraop_mr:
                    self.intraop_mr.append(name)
                    self.intraop_mr_lower.append(name.lower())

                elif i == 3 and name.lower() not in self.segmentations_lower:
                    self.segmentations.append(name)
                    self.segmentations_lower.append(name.lower())

                elif i == 3 and name.lower() not in self.segmentations:
                    self.segmentations.append(name)
                    self.segmentations_lower.append(name.lower())

    def export_multiple_scenes(self, mrb_paths, export_path=None):

        mrb_paths = StructureLogic.return_a_list_of_all_mrbs_in_a_folder(mrb_paths)

        # loop through all mrbs to get their statistics
        for mrb_path in mrb_paths:
            # load mrb
            slicer.mrmlScene.Clear()

            try:
                slicer.util.loadScene(mrb_path)
            except Exception as e:
                pass

            self.multiple_folder_structures.append(StructureLogic.bfs_generate_folder_structure_as_tree())

            slicer.mrmlScene.Clear()

        if export_path is None:  # then just print the stats
            self.combine_trees()

            print("Preop MR:")
            for preop_mr in self.preop_mr:
                print(f"\t{preop_mr}")

            print("\n")

            print("Intraop MR:")
            for intraop_mr in self.intraop_mr:
                print(f"\t{intraop_mr}")

