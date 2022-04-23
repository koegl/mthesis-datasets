import slicer
import vtk

import os

from AdditionalLogic.tree import Tree

class StructureLogic:
    """
    Class to encapsulate logic for handling mrb/folder structure
    """

    def __init__(self):
        pass

    @staticmethod
    def bfs_generate_folder_structure_as_tree():
        """
        Generate the folder structure as a tree
        """
        # create a list with children and get the subject node
        child_ids = vtk.vtkIdList()
        subject_hierarchy_node = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
        subject_hierarchy_node.GetItemChildren(subject_hierarchy_node.GetSceneItemID(), child_ids)
        sh_id_patient = child_ids.GetId(0)

        # FIFO queue of nodes and create root
        folder_structure = Tree(subject_hierarchy_node.GetItemName(sh_id_patient), sh_id=sh_id_patient, vtk_id="")
        # vtk_id is None because only volumes have it
        visited = [sh_id_patient]  # array to store visited IDs
        nodes_queue = [folder_structure]

        while nodes_queue:
            # dequeue node
            s = nodes_queue.pop(0)

            # get all children of the dequeued node s and add to queue if not visited
            subject_hierarchy_node.GetItemChildren(s.sh_id, child_ids)

            # check if it is not a segment (we continue when we are at a segmentation, because we don't want to add its
            # segments to the tree
            if "segmentationnode" in s.vtk_id.lower():
                continue

            for i in range(child_ids.GetNumberOfIds()):
                sub_id = child_ids.GetId(i)
                if sub_id not in visited:
                    sub_name = subject_hierarchy_node.GetItemName(sub_id)
                    sub_vtk_node = subject_hierarchy_node.GetItemDataNode(sub_id)
                    if sub_vtk_node:
                        sub_vtk_id = sub_vtk_node.GetID()
                    else:
                        sub_vtk_id = ""

                    sub_child = s.add_child(Tree(sub_name, sh_id=sub_id, vtk_id=sub_vtk_id))  # this returns the node
                    # which is like a C++ reference, so we can use this in the next iteration to append nodes
                    nodes_queue.append(sub_child)
                    visited.append(sub_id)

        return folder_structure

    @staticmethod
    def return_a_list_of_all_mrbs_in_a_folder(folder_path):
        """
        Returns a list of all mrbs in a folder.
        :@param folder_path: Path to the folder in which to search for mrbs.
        :@return: A list of all mrbs in the folder.
        """

        # check if the path is valid
        if not os.path.isdir(folder_path):
            raise Exception("The mrb folder path is not valid.")

        mrbs = []

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith(".mrb"):
                    mrbs.append(os.path.join(root, file))

        return mrbs
