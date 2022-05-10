import slicer
from DICOMLib import DICOMUtils

from Resources.Logic.loading_logic import LoadingLogic
from Resources.Logic.structure_logic import StructureLogic

import os


class DicomLoadingLogic(LoadingLogic):
    """
    Logic class for loading DICOM files.
    """
    # - probably duplicate the original structure and then only work on the new one
    # todo Move the segmentations to a separate study
    # todo Load everything as folders not as studies
    # todo open popup windows saying that the file is loading
    # todo close popup windows after 5 s
    # todo reorder items in the tree with sh.MoveItem()

    def __init__(self, load_path, patient_dicom_id, landmark_path):
        super().__init__()

        self.load_path = load_path
        self.patient_dicom_id = patient_dicom_id
        self.landmark_path = landmark_path

        self.landmark_node = None
        self.loaded_volumes_vtk_ids = []
        self.study_structure = None

        self.sh_node = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)

    def load_all_dicom_data(self):

        # get acces to the dicom database
        db = slicer.dicomDatabase

        # import the directory to the database
        DICOMUtils.importDicom(self.load_path, db)

        # load all the data from the loaded patient to the scene
        self.loaded_volumes_vtk_ids = DICOMUtils.loadPatientByPatientID(self.patient_dicom_id)

    def clean_up_names(self):
        for study_name, study in self.study_structure.children.items():

            # remove date and parenthesis from the name
            # split name by space
            split_name = study_name.split(' ')

            # remove elements with parenthesis and create a new list without those elements
            new_name = []
            for element in split_name:
                if '(' not in element and ')' not in element:
                    new_name.append(element)

            # join the list back to a string
            new_name = ' '.join(new_name)
            self.sh_node.SetItemName(study.sh_id, new_name)
            study.name = new_name

            # remove number and colon from the name
            for volume_name, volume in study.children.items():
                temp_volume_node = slicer.mrmlScene.GetNodeByID(volume.vtk_id)
                while ':' in volume_name[0:3]:
                    volume_name = volume_name[3:]
                    temp_volume_node.SetName(volume_name)
                    volume.name = volume_name

        self.study_structure = StructureLogic.bfs_generate_folder_structure_as_tree()

    def collapse_segmentations(self):

        # loop through all volumes
        for study_name, study in self.study_structure.children.items():
            for volume_name, volume in study.children.items():
                if "segmentationnode" in volume.vtk_id.lower():
                    segmentation_node = slicer.util.getNode(volume.vtk_id)
                    segmentation_node_sh_id = self.sh_node.GetItemByDataNode(segmentation_node)
                    self.sh_node.SetItemExpanded(segmentation_node_sh_id, False)

    def segmentations_outlines(self):
        for study_name, study in self.study_structure.children.items():
            for volume_name, volume in study.children.items():
                if "segmentationnode" in volume.vtk_id.lower():
                    segmentation_node = slicer.mrmlScene.GetNodeByID(volume.vtk_id)
                    segmentation_node.GetDisplayNode().SetAllSegmentsOpacity2DFill(False)

    def reorder_studies_into_directories(self):
        for study_name, study in self.study_structure.children.items():

            # create new folder
            new_folder_sh_id = self.sh_node.CreateFolderItem(self.sh_node.GetSceneItemID(), study_name)

            # assign children to new folder
            for volume_name, volume in study.children.items():
                self.sh_node.SetItemParent(volume.sh_id, new_folder_sh_id)

            # remove study
            self.sh_node.RemoveItem(study.sh_id)

        self.study_structure = StructureLogic.bfs_generate_folder_structure_as_tree()

    def postprocess_loaded_dicoms_and_landmarks(self):
        self.study_structure = StructureLogic.bfs_generate_folder_structure_as_tree()

        self.clean_up_names()

        self.collapse_segmentations()

        self.segmentations_outlines()

        self.reorder_studies_into_directories()

        print(5)

    def load_structure(self):

        self.load_all_dicom_data()

        if self.landmark_path != "":
            self.landmark_node = slicer.util.loadMarkups(self.landmark_path)

        self.postprocess_loaded_dicoms_and_landmarks()

        slicer.util.selectModule("AmigoDataset")