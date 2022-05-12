import slicer
import vtk

from Resources.Logic.tree import Tree
from Resources.Logic.utils import np_to_vtk, vtk_to_np
from Resources.Logic.structure_logic import StructureLogic

import os
import hashlib
import numpy as np


class ExportingLogic:
    """
    Class to encapsulate logic for exporting a scene. Assumed structure:
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
        └── Landmarks
    """

    def __init__(self, output_folder=None):

        self.deidentify = None
        self.resample_size = None
        self.identity = None

        if output_folder is None:
            self.output_folder = os.getcwd()
        else:
            self.output_folder = output_folder

        self.subject_folder = None

        self.patient_id = None

        self.folder_structure_parent = None

    def generate_id(self, hash_string, deidentify=False):
        """
        Generates a unique id by hashing hash_string. (unique up to 999999999)
        @param hash_string: The path which will be hashed
        @param deidentify: If True, the hash will be de-identified
        @return: the id
        """

        if deidentify is False:
            # get filename from mrb_path without extension
            mrb_path = slicer.mrmlScene.GetURL()
            mrb_path = mrb_path.split("/")
            mrb_name = mrb_path[-1]
            mrb_name = mrb_name.split(".")[0]

            # mrb name might be empty if we haven't loaded a mrb but single files (like with the load function)
            if mrb_name == "":
                child_ids = vtk.vtkIdList()
                subject_hierarchy_node = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
                subject_hierarchy_node.GetItemChildren(subject_hierarchy_node.GetSceneItemID(), child_ids)
                sh_patient_id = child_ids.GetId(0)
                mrb_name = subject_hierarchy_node.GetItemName(sh_patient_id)

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

    def export_landmarks_to_json(self, folder_path):
        """
        Export landmark to json
        """

        bfs_array = Tree.bfs(self.folder_structure_parent)

        for node in bfs_array:
            try:
                if "markupsfiducialnode" in node.vtk_id.lower():

                    markups_node = slicer.mrmlScene.GetNodeByID(node.vtk_id)

                    if markups_node is None:
                        raise ValueError(f"Could not find and export landmarks node {node.name}")

                    slicer.util.saveNode(markups_node, os.path.join(folder_path, "landmarks.json"))

            except Exception as e:
                slicer.util.errorDisplay(f"Could not export node {node.name}.\n({str(e)})\n"
                                         f"export_landmarks_to_json",
                                         windowTitle="Json export error")

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

    def harden_transformations(self):
        """
        Hardens all transformations
        """

        all_nodes = Tree.bfs(self.folder_structure_parent)

        for node in all_nodes:
            # harden transformation
            buf_node = slicer.mrmlScene.GetNodeByID(node.vtk_id)

            if buf_node:  # if it exists
                try:
                    buf_node.HardenTransform()
                except:  # broad clause, but some nodes cannot be transformed and we don't want to crash
                    pass

    def transform_all_nodes_to_identity(self):

        # todo this should also transform the landmarks

        # get all nodes from the scene tree
        all_nodes = Tree.bfs(self.folder_structure_parent)

        # get the main node to which everything will be transformed
        main_node = slicer.util.getFirstNodeByName(self.identity)
        if main_node is None:
            return "Could not find parent identity node - wrong name. Export will continue after clicking ok without " \
                   "any transformations applied"

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

        # transform all other nodes with the inverse of the main node (volumes and segmentations)
        for node in all_nodes:
            if node.vtk_id != main_node.GetID() and node.vtk_id and "markupsfiducial" not in node.vtk_id.lower():
                # combine the two transformations
                current_transform = vtk.vtkMatrix4x4()
                slicer_node = slicer.mrmlScene.GetNodeByID(node.vtk_id)
                slicer_node.GetIJKToRASMatrix(current_transform)
                current_transform = vtk_to_np(current_transform)
                new_transform = np.dot(inverse_main_original_transform, current_transform)

                new_transform = np.dot(identity_transform_reflection_yz, new_transform)

                # set the combined transformation
                slicer_node.SetIJKToRASMatrix(np_to_vtk(new_transform))

            # transform landmarks
            elif node.vtk_id != main_node.GetID() and node.vtk_id and "markupsfiducial" in node.vtk_id.lower():
                slicer_node = slicer.mrmlScene.GetNodeByID(node.vtk_id)
                new_transform = np.dot(identity_transform_reflection_yz, inverse_main_original_transform)
                slicer_node.ApplyTransformMatrix(np_to_vtk(new_transform))

        return ""

    def resample_all_nodes(self):

        # get all nodes from the scene tree
        all_nodes = Tree.bfs(self.folder_structure_parent)

        # create a reference node with the correct spacing
        reference_node = self.create_node_with_correct_spacing(self.resample_size)

        # loop thorugh all nodes and use the brainsresample CLI to resampple them to the correct spacing (ref node)
        for node in all_nodes:
            if "vtkMRMLScalarVolumeNode" in node.vtk_id:
                vtk_node = slicer.mrmlScene.GetNodeByID(node.vtk_id)
                parameters = {'inputVolume': vtk_node, 'referenceVolume': reference_node, 'outputVolume': vtk_node}
                slicer.cli.run(slicer.modules.brainsresample, None, parameters,
                               wait_for_completion=True, update_display=False)

        # remove the reference node
        slicer.mrmlScene.RemoveNode(reference_node)

    def preprocess_nodes(self):
        self.harden_transformations()

        # #. Transform all to identity of parent volume
        if self.identity:
            result = self.transform_all_nodes_to_identity()

            if result:
                slicer.util.errorDisplay(f"Couldn't transform all nodes to parent identity.\n{result}",
                                         windowTitle="Transform error")

        # #. Resample all nodes to the same size
        if self.resample_size:
            self.resample_all_nodes()

    def export_data(self):
        raise NotImplementedError("export_data method is not implemented in the Parent class.")

    def full_export(self, identity=False, resample_size=False, deidentify=False):
        """
        Perform all the steps to export the current scene
        """

        self.identity = identity
        self.resample_size = resample_size
        self.deidentify = deidentify

        # 1. Generate folder structure
        self.folder_structure_parent = StructureLogic.bfs_generate_folder_structure_as_tree()

        # 2. Preprocess nodes
        self.preprocess_nodes()

        # 3. Export data
        self.export_data()
