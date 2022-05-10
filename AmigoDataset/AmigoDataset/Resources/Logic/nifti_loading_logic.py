import slicer

from Resources.Logic.loading_logic import LoadingLogic
from Resources.Logic.structure_logic import StructureLogic
from Resources.Logic.dicom_exporting_logic import DicomExportingLogic

import os


# todo reorder items in the tree with sh.MoveItem()
class NiftiLoadingLogic(LoadingLogic):
    def __init__(self, load_path):
        super().__init__()
        self.load_path = load_path

    def load_structure(self):
        # load folder structure
        folders = []
        buf = os.listdir(self.load_path)
        for folder in buf:
            if "store" not in folder.lower() and os.path.isdir(os.path.join(self.load_path, folder)):
                folders.append(folder)

        hierarchy_node = slicer.mrmlScene.GetSubjectHierarchyNode()

        # create patient
        # get last folder name from folder_structure_path
        subject_folder_id = os.path.basename(os.path.normpath(self.load_path))
        patient_id = hierarchy_node.CreateSubjectItem(hierarchy_node.GetSceneItemID(), subject_folder_id)

        # create folder structure and load nifti files into it
        for data_folder in folders:
            data_folder_id = hierarchy_node.CreateFolderItem(hierarchy_node.GetSceneItemID(), data_folder)
            hierarchy_node.SetItemParent(data_folder_id, patient_id)
            data_folder_path = os.path.join(self.load_path, data_folder)

            # for all nifti files in the folder
            for root, dirs, files in os.walk(data_folder_path):
                for file in files:
                    if file.endswith(".nii") or file.endswith(".json"):
                        temp_path = os.path.join(root, file)

                        if "annotations" in temp_path.lower():
                            temp_volume_node = self.load_annotation(temp_path)
                        else:
                            temp_volume_node = slicer.util.loadVolume(temp_path)

                        temp_volume_hierarchy_id = hierarchy_node.GetItemByDataNode(temp_volume_node)
                        hierarchy_node.SetItemParent(temp_volume_hierarchy_id, data_folder_id)

        # assign correct parents to the segmentations
        folder_structure = StructureLogic.bfs_generate_folder_structure_as_tree()
        volume_list = folder_structure.bfs(folder_structure)

        for volume in volume_list:
            if "annotations" in volume.parent.name.lower() and "landmark" not in volume.name.lower():
                parent = DicomExportingLogic.find_semantic_parent_of_a_segmentation(volume.name,
                                                                                                          folder_structure,
                                                                                                          "Pre-op MR")
                parent_node = slicer.mrmlScene.GetNodeByID(parent.vtk_id)

                if parent is not None:
                    volume_node = slicer.mrmlScene.GetNodeByID(volume.vtk_id)
                    volume_node.SetReferenceImageGeometryParameterFromVolumeNode(parent_node)
