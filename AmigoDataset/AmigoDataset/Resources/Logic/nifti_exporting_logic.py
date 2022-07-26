import slicer

from Resources.Logic.exporting_logic import ExportingLogic
from Resources.Logic.tree import Tree
from Resources.Logic.structure_logic import StructureLogic
from Resources.Logic import utils

import os


class NiftiExportingLogic(ExportingLogic):
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
        └── Landmarks
    """

    def __init__(self, output_folder=None):
        super().__init__(output_folder)

        self.annotations_folder = ""

        self.folder_structure = StructureLogic.bfs_generate_folder_structure_as_tree()
        self.subject_hierarchy = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)

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
        self.patient_id = self.generate_id(self.folder_structure.name, self.deidentify)

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

                    if "annotations" in node.name.lower():
                        self.annotations_folder = buf_folder

        # loop through all nodes to export them to nifti
        for node in bfs_array:
            try:  # only if it: does not have any children; is not a transformation;
                if not bool(node.children) \
                        and "transform" not in node.name.lower() \
                        and "landmark" not in node.parent.name.lower():

                    parent_path = os.path.join(self.subject_folder, node.parent.name)
                    file_name = f"case{self.case_number}-{node.name}.nii"
                    file_name = file_name.replace(" ", "-")
                    export_path = os.path.join(parent_path, file_name)

                    self.export_node_to_nifti(export_path, node.vtk_id)

            except Exception as e:
                slicer.util.errorDisplay(f"Could not export node {node.name}. ({str(e)})")

    def export_data(self):

        self.export_volumes_and_segmentations_to_nifti()

        self.export_landmarks_to_json(self.annotations_folder)

        utils.collapse_segmentations(self.folder_structure, self.subject_hierarchy)
