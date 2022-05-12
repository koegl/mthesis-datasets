import os
import vtk
import slicer
import numpy as np


def extract_mrb_paths(directory_path="/Users/fryderykkogl/Dropbox (Partners HealthCare)/TCIA/TCIA cases ALL"):
    """
    Function to extract all .mrb files from a directory and its sub-directories
    @param directory_path: Path to the root directory
    @return: a list of all paths
    """
    mrb_paths = []

    for path, subdirs, files in os.walk(directory_path):
        for name in files:
            if ".mrb" in name:
                mrb_paths.append(os.path.join(path, name))

    return mrb_paths


def np_to_vtk(np_array):
    m = vtk.vtkMatrix4x4()
    m.DeepCopy(np_array.ravel())
    return m


def vtk_to_np(vtk_matrix):
    b = np.zeros((4, 4))
    vtk_matrix.DeepCopy(b.ravel(), vtk_matrix)
    return b


def find_semantic_parent_of_a_segmentation(segmentation_name, folder_structure, pre_op_name):
        """
        Function to find the semantic parent of a segmentation - semantic referring to the fact that we are not looking
        at the hierarchy tree, as the segmentaion will be in a different folder. What we are doing instead is only look
        at the pre-operative imaging (that's where the lesions were created) and find the volume which corresponds to
        the segmentation
        @param segmentation_name: The name of the segmentation
        @param folder_structure: The folder structure of the scene
        @param pre_op_name: The name of the pre-operative imaging folder
        @return: The volume node of the parent
        """
        # todo - assign to flair

        first_node = None

        if "t2" in segmentation_name.lower():
            # loop through pre-op imaging nodes
            for preop_name, preop_node in folder_structure.children[pre_op_name].children.items():
                if "t2" in preop_name.lower():
                    return preop_node

        else:
            # loop through pre-op imaging nodes
            for preop_name, preop_node in folder_structure.children[pre_op_name].children.items():

                if not first_node:
                    first_node = preop_node

                if "t1" in preop_name.lower():
                    return preop_node

        # this case can happen when t2 is in the segmentation name but in none of the pre-op names
        if not first_node:
            for preop_name, preop_node in folder_structure.children[pre_op_name].children.items():
                if not first_node:
                    first_node = preop_node

                if "t1" in preop_name.lower():
                    return preop_node

        # if no t1 or t2 is found, return the first pre-op node
        return first_node


def collapse_segmentations(study_structure, sh_node):

    # loop through all volumes
    for study_name, study in study_structure.children.items():
        for volume_name, volume in study.children.items():
            if "segmentationnode" in volume.vtk_id.lower():
                segmentation_node = slicer.util.getNode(volume.vtk_id)
                segmentation_node_sh_id = sh_node.GetItemByDataNode(segmentation_node)
                sh_node.SetItemExpanded(segmentation_node_sh_id, False)
