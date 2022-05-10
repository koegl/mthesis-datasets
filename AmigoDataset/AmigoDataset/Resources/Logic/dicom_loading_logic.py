import slicer
from DICOMLib import DICOMUtils

from Resources.Logic.loading_logic import LoadingLogic

import os


class DicomLoadingLogic(LoadingLogic):
    """
    Logic class for loading DICOM files.
    """

    def __init__(self, load_path, patient_dicom_id, landmark_path):
        super().__init__()

        self.load_path = load_path
        self.patient_dicom_id = patient_dicom_id
        self.landmark_path = landmark_path

        self.landmark_node = None
        self.loaded_volumes_vtk_ids = []

    def load_all_dicom_data(self):
        # instantiate a new DICOM browser
        dicom_browser = slicer.modules.DICOMWidget.browserWidget.dicomBrowser

        dicom_browser.importDirectory(self.load_path, dicom_browser.ImportDirectoryAddLink)

        # wait for import to finish before proceeding
        dicom_browser.waitForImportFinished()

        # load all the data from the loaded patient to the scene
        self.loaded_volumes_vtk_ids = DICOMUtils.loadPatientByPatientID(self.patient_dicom_id)

    def postprocess_loaded_dicoms_and_landmarks(self):
        pass

    def load_structure(self):

        self.load_all_dicom_data()

        self.landmark_node = slicer.util.loadMarkups(self.landmark_path)

        self.postprocess_loaded_dicoms_and_landmarks()

        slicer.util.selectModule("AmigoDataset")