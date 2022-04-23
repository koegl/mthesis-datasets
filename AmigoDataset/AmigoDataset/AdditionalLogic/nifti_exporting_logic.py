import slicer
import vtk
import DICOMLib

from AdditionalLogic.tree import Tree
from AdditionalLogic.utils import np_to_vtk, vtk_to_np

import os
import hashlib
import logging
import numpy as np


class NiftiExportingLogic:
    """
    Class to encapsulate logic for exporting a scene to nifti. Assumed structure:
    Scene
    └── Subject name/mrn
        ├── Pre-op MR
        │   └── volumes
        ├── Intra-op US
        │   └── volumes
        ├── Intra-op MR
        │   └── volumes
        ├── Segmentation
        │   └── lesion segmentation
        └── Annotations
            └── landmarks
    """

    def __init__(self, output_folder=None, log_path="/Users/fryderykkogl/Desktop/log.log", deidentify=False):

        if output_folder is None:
            self.output_folder = os.getcwd()
        else:
            self.output_folder = output_folder

        self.deidentify = deidentify

        self.subject_folder = None

        self.patient_id = None

        self.folder_structure = None

        logging.basicConfig(filename=log_path)
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)  # lowest level from ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')

        self.pre_op_name = ""

    def bfs_generate_folder_structure_as_tree(self):
        """
        Generate the folder structure as a tree
        """
        # create a list with children and get the subject node
        child_ids = vtk.vtkIdList()
        subject_hierarchy_node = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
        subject_hierarchy_node.GetItemChildren(subject_hierarchy_node.GetSceneItemID(), child_ids)
        sh_id_patient = child_ids.GetId(0)

        # FIFO queue of nodes and create root
        self.folder_structure = Tree(subject_hierarchy_node.GetItemName(sh_id_patient), sh_id=sh_id_patient, vtk_id="")
        # vtk_id is None because only volumes have it
        visited = [sh_id_patient]  # array to store visited IDs
        nodes_queue = [self.folder_structure]

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

                    if "pre" in sub_name.lower() and "op" in sub_name.lower() and "imaging" in sub_name.lower():
                        self.pre_op_name = sub_name

                    sub_child = s.add_child(Tree(sub_name, sh_id=sub_id, vtk_id=sub_vtk_id))  # this returns the node
                    # which is like a C++ reference, so we can use this in the next iteration to append nodes
                    nodes_queue.append(sub_child)
                    visited.append(sub_id)

    def harden_transformations(self):
        """
        Hardens all transformations
        """

        all_nodes = Tree.bfs(self.folder_structure)

        for node in all_nodes:
            # harden transformation
            buf_node = slicer.mrmlScene.GetNodeByID(node.vtk_id)

            if buf_node:  # if it exists
                try:
                    buf_node.HardenTransform()
                except:  # broad clause, but some nodes cannot be transformed and we don't want to crash
                    pass

    def generate_id(self, hash_string):
        """
        Generates a unique id by hashing hash_string. (unique up to 999999999)
        @param hash_string: The path which will be hashed
        @return: the id
        """

        if self.deidentify is False:
            # get filename from mrb_path without extension
            mrb_path = slicer.mrmlScene.GetURL()
            mrb_path = mrb_path.split("/")
            mrb_name = mrb_path[-1]
            mrb_name = mrb_name.split(".")[0]

            return mrb_name

        # create hasher
        hasher = hashlib.sha1()

        # hash the string
        hasher.update(hash_string.encode('utf-8'))

        # return hex-string of hashed value
        hex_string = hasher.hexdigest()

        # convert to int base 10
        hashed = int(hex_string, 16)

        # take the mod with a prime number to reduce the size of the id
        hashed_mod = hashed % 999999937

        return str(hashed_mod)

    @staticmethod
    def export_node_to_nifti(export_path=None, volume_vtk_id=None):
        """
        Function that exports a given scalar volume to nifti at the provided export path
        @param export_path: Path (includfing file name) to where the nifti will be saved
        @param volume_vtk_id: The volume which will be saved
        @return: True if success, false otherwise
        """

        node = slicer.mrmlScene.GetNodeByID(volume_vtk_id)

        # if its a volume node save it directly
        if "volumenode" in node.GetID().lower():
            slicer.util.saveNode(node, export_path)
            return

        # if its a segmentation node convert it to a labelmap first and then save it
        elif "segmentationnode" in node.GetID().lower():
            reference_volume_node = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
            labelmap_volume_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLabelMapVolumeNode")
            slicer.modules.segmentations.logic().ExportVisibleSegmentsToLabelmapNode(node,
                                                                                     labelmap_volume_node,
                                                                                     reference_volume_node)
            slicer.util.saveNode(labelmap_volume_node, export_path)
            slicer.mrmlScene.RemoveNode(labelmap_volume_node.GetDisplayNode().GetColorNode())
            slicer.mrmlScene.RemoveNode(labelmap_volume_node)
            return
        else:
            return

    def export_volumes_and_segmentations_to_nifti(self):
        """
        Export volumes according to the created structure to Nifti
        """

        bfs_array = Tree.bfs(self.folder_structure)

        # generate subject id
        self.patient_id = self.generate_id(self.folder_structure.name)

        # create subject folder
        self.subject_folder = os.path.join(self.output_folder, self.patient_id)
        if not os.path.exists(self.subject_folder):
            os.makedirs(self.subject_folder)

        # create study folders
        for node in bfs_array:
            if bool(node.children):  # if it has children, create a folder with its name
                buf_folder = os.path.join(self.subject_folder, node.name)
                if not os.path.exists(buf_folder):
                    os.makedirs(buf_folder)

        # loop through all nodes to export them to nifti
        for node in bfs_array:
            try:  # only if it: does not have any children; is not a transformation;
                if not bool(node.children) \
                        and "transform" not in node.name.lower() \
                        and "landmark" not in node.parent.name.lower():

                    parent_path = os.path.join(self.subject_folder, node.parent.name)
                    export_path = os.path.join(parent_path, node.name + ".nii")

                    self.export_node_to_nifti(export_path, node.vtk_id)

            except Exception as e:
                self.logger.log(logging.ERROR, f"Could not export node {node.name}. ({str(e)})")

    def export_landmarks_to_fcsv(self):
        """
        Export landmark to fcsv
        """
        # todo export like Andras has shown on discourse
        bfs_array = Tree.bfs(self.folder_structure)

        counter = {}
        for node in bfs_array:
            try:
                if not bool(node.children) \
                        and "transform" not in node.name.lower() \
                        and "segment" not in node.parent.name.lower() \
                        and "landmark" in node.parent.name.lower():

                    # increase/create counter for series number
                    if node.parent.name in counter:
                        counter[node.parent.name] += 1
                    else:
                        counter[node.parent.name] = 1

                    markups_node = slicer.mrmlScene.GetNodeByID(node.vtk_id)

                    if markups_node is None:
                        raise ValueError(f"Could not find and export landmarks node {node.name}")

                    slicer.util.saveNode(markups_node,
                                         os.path.join(self.subject_folder,
                                                      "landmarks_" + "uid"))  # todo self.study_instance_uid))
            except Exception as e:
                self.logger.log(logging.ERROR, f"Could not export node {node.name}.\n({str(e)})\n"
                                               f"export_landmarks_to_fcsv")

    def transform_all_nodes_to_identity(self, identity_main_name):

        # get all nodes from the scene tree
        all_nodes = Tree.bfs(self.folder_structure)

        # get the main node to which everything will be transformed
        main_node = slicer.util.getFirstNodeByName(identity_main_name)
        if main_node is None:
            return "Could not find identity node - wrong name"

        # get its transform and create the inverse (with negative y and z)
        main_original_transform = vtk.vtkMatrix4x4()
        main_node.GetIJKToRASMatrix(main_original_transform)
        main_original_transform = vtk_to_np(main_original_transform)
        inverse_main_original_transform = np.linalg.inv(main_original_transform)

        # create identity with y and z negative
        identity_transform_reflection_yz = np.eye(4)
        identity_transform_reflection_yz[1, 1] = -1
        identity_transform_reflection_yz[2, 2] = -1

        # transform the main node to identity (replace matrices)
        main_node.SetIJKToRASMatrix(np_to_vtk(identity_transform_reflection_yz))

        # transform all other nodes with the inverse of the main node
        for node in all_nodes:
            if node.vtk_id != main_node.GetID() and node.vtk_id:

                # combine the two transformations
                current_transform = vtk.vtkMatrix4x4()
                slicer_node = slicer.mrmlScene.GetNodeByID(node.vtk_id)
                slicer_node.GetIJKToRASMatrix(current_transform)
                current_transform = vtk_to_np(current_transform)
                new_transform = np.dot(inverse_main_original_transform, current_transform)

                new_transform = np.dot(identity_transform_reflection_yz, new_transform)

                # set the combined transformation
                slicer_node.SetIJKToRASMatrix(np_to_vtk(new_transform))

        return ""

    @staticmethod
    def create_node_with_correct_spacing(spacing=0.5):
        node_name = "sampling_ref"
        image_size = [256, 256, 176]
        voxel_type = vtk.VTK_UNSIGNED_CHAR
        image_origin = [0.0, 0.0, 0.0]
        image_spacing = [spacing, spacing, spacing]
        image_directions = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        fill_voxel_value = 0

        # Create an empty image volume, filled with fill_voxel_value
        image_data = vtk.vtkImageData()
        image_data.SetDimensions(image_size)
        image_data.AllocateScalars(voxel_type, 1)
        image_data.GetPointData().GetScalars().Fill(fill_voxel_value)
        # Create volume node
        volume_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode", node_name)
        volume_node.SetOrigin(image_origin)
        volume_node.SetSpacing(image_spacing)
        volume_node.SetIJKToRASDirections(image_directions)
        volume_node.SetAndObserveImageData(image_data)
        volume_node.CreateDefaultDisplayNodes()
        volume_node.CreateDefaultStorageNode()

        return volume_node
    
    def resample_all_nodes(self, resample_size):

        # get all nodes from the scene tree
        all_nodes = Tree.bfs(self.folder_structure)

        # create a reference node with the correct spacing
        reference_node = self.create_node_with_correct_spacing(resample_size)

        # loop thorugh all nodes and use the brainsresample CLI to resampple them to the correct spacing (ref node)
        for node in all_nodes:
            if "vtkMRMLScalarVolumeNode" in node.vtk_id:
                vtk_node = slicer.mrmlScene.GetNodeByID(node.vtk_id)
                parameters = {'inputVolume': vtk_node, 'referenceVolume': reference_node, 'outputVolume': vtk_node}
                slicer.cli.run(slicer.modules.brainsresample, None, parameters,
                               wait_for_completion=True, update_display=False)

        # remove the reference node
        slicer.mrmlScene.RemoveNode(reference_node)

    def full_export(self, identity=False, resample_size=False):
        """
        Perform all the steps to export the current scene
        """

        # 1. Generate folder structure
        self.bfs_generate_folder_structure_as_tree()

        # 3. Harden transforms
        self.harden_transformations()

        # #. Transform all to identity of parent volume
        if identity:
            result = self.transform_all_nodes_to_identity(identity)

            if result:
                slicer.util.errorDisplay(f"Couldn't export current scene/mrb to Nifti.\n{result}",
                                         windowTitle="Export error")
                return

        # #. Resample all nodes to the same size
        if resample_size:
            self.resample_all_nodes(resample_size)

        # 3. Export volumes according to the studies
        self.export_volumes_and_segmentations_to_nifti()

        # 5. Export landmarks
        self.export_landmarks_to_fcsv()
