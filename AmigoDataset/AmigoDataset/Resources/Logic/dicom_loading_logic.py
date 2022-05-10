import slicer
from DICOMLib import DICOMUtils

from Resources.Logic.loading_logic import LoadingLogic
from Resources.Logic.structure_logic import StructureLogic

import os


class DicomLoadingLogic(LoadingLogic):
    """
    Logic class for loading DICOM files.
    """
    # todo Make it so that in DICOM the original structure is preserved
    # - probably duplicate the original structure and then only work on the new one
    # todo Remove date from study name
    # todo Remove the stuff in the parentheesis
    # todo Move the segmentations to a separate study
    # todo Load everything as folders not as studies
    # todo close popup windows after 5 s

    def __init__(self, load_path, patient_dicom_id, landmark_path):
        super().__init__()

        self.load_path = load_path
        self.patient_dicom_id = patient_dicom_id
        self.landmark_path = landmark_path

        self.landmark_node = None
        self.loaded_volumes_vtk_ids = []
        self.study_structure = None

    def load_all_dicom_data(self):

        # get acces to the dicom database
        db = slicer.dicomDatabase

        # import the directory to the database
        DICOMUtils.importDicom(self.load_path, db)

        # load all the data from the loaded patient to the scene
        self.loaded_volumes_vtk_ids = DICOMUtils.loadPatientByPatientID(self.patient_dicom_id)

    def remove_letter_and_colon_from_volume_names(self):
        for study_name, study in self.study_structure.children.items():
            for volume_name, volume in study.children.items():
                temp_node = slicer.util.getNode(volume.vtk_id)
                while ':' in volume_name[0:3]:
                    volume_name = volume_name[3:]
                    temp_node.SetName(volume_name)
                    volume.name = volume_name

        self.study_structure = StructureLogic.bfs_generate_folder_structure_as_tree()

    def remove_numbers_from_studies_parenthesis(self):
        # todo
        for study_name, study in self.study_structure.children.items():
            pass

    def collapse_segmentations(self):
        subject_hierarchy_node = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)

        # loop through all volumes
        for study_name, study in self.study_structure.children.items():
            for volume_name, volume in study.children.items():
                if "segmentationnode" in volume.vtk_id.lower():
                    segmentation_node = slicer.util.getNode(volume.vtk_id)
                    segmentation_node_sh_id = subject_hierarchy_node.GetItemByDataNode(segmentation_node)
                    subject_hierarchy_node.SetItemExpanded(segmentation_node_sh_id, False)
    def segmentations_outlines(self):
        for study_name, study in self.study_structure.children.items():
            for volume_name, volume in study.children.items():
                if "segmentationnode" in volume.vtk_id.lower():
                    segmentation_node = slicer.mrmlScene.GetNodeByID(volume.vtk_id)
                    segmentation_node.GetDisplayNode().SetAllSegmentsOpacity2DFill(False)

    def postprocess_loaded_dicoms_and_landmarks(self):
        self.study_structure = StructureLogic.bfs_generate_folder_structure_as_tree()

        self.remove_letter_and_colon_from_volume_names()

        self.remove_numbers_from_studies_parenthesis()

        self.collapse_segmentations()

        self.segmentations_outlines()

        print(5)

    def load_structure(self):

        self.load_all_dicom_data()

        if self.landmark_path != "":
            self.landmark_node = slicer.util.loadMarkups(self.landmark_path)

        self.postprocess_loaded_dicoms_and_landmarks()

        slicer.util.selectModule("AmigoDataset")