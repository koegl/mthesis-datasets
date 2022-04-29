import slicer
import DICOMScalarVolumePlugin
import DICOMSegmentationPlugin
from DICOMLib import DICOMUtils
import DICOMLib

from Resources.Logic.exporting_logic import ExportingLogic
from Resources.Logic.tree import Tree

import os


class DicomExportingLogic(ExportingLogic):
    """
    Class to encapsulate logic for exporting a scene to DICOM. Assumed structure:
    Scene
    └── Subject name/mrn
        ├── Pre-op imaging
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
        self.study_instance_uid = None
        self.pre_op_name = "Pre-op MR"

    def create_studies_in_slicer(self):
        """
        Create studies according to the folder structure in Slicer
        """
        hierarchy_node = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)

        # create studies
        for _, child in self.folder_structure.children.items():
            if 'transform' in child.name.lower():  # we don't want to create a study for the transform
                continue
            child.sh_study_id = hierarchy_node.CreateStudyItem(self.folder_structure.sh_id, child.name)
            hierarchy_node.SetItemParent(child.sh_study_id, self.folder_structure.sh_id)

        # loop through all nodes in BFS order
        bfs_array_of_nodes = Tree.bfs(self.folder_structure)
        for node in bfs_array_of_nodes:
            if node.sh_study_id is None and 'transform' not in node.name.lower():  # true if the node is not a study -> a series
                hierarchy_node.SetItemParent(node.sh_id, node.parent.sh_study_id)

    def create_subject_folder(self):
        """
        :@param subject_id: the subject id
        :return: the subject folder§
        Function that create a new folder named with the id of the subject in the output folder
        """
        self.subject_folder = os.path.join(self.output_folder, self.patient_id)

        if not os.path.exists(self.subject_folder):
            os.makedirs(self.subject_folder)

    def set_dicom_tags(self, exp, file, series_counter=1, segmentation=None):
        """
        Sets dicom tags of one exportable exp
        @param exp: The exportable
        @param file: The file in the hierarchy tree
        @param series_counter: Counts at which series we currently are
        @param segmentation: A node with a parent - only available if we have a segmentation
        """
        # PatientID - get last element of subject name (MRN) and hash it - root name
        self.patient_id = self.generate_id(self.folder_structure.name, self.deidentify)
        exp.setTag('PatientID', self.patient_id)
        exp.setTag('PatientName', self.patient_id)

        # create a directory to save the patient dicoms
        self.create_subject_folder()

        # output folder
        exp.directory = self.subject_folder

        # StudyDescription (name of the study in the hierarchy)
        study_description = file.parent.name
        exp.setTag('StudyDescription', study_description)

        # If any of UIDs (studyInstanceUID, seriesInstanceUID, and frameOfReferenceInstanceUID) are specified then all
        # of them must be specified.
        # StudyInstanceUID (unique for each study, series are grouped by this ID)
        self.study_instance_uid = self.generate_id(study_description + self.folder_structure.name, deidentify=True)
        exp.setTag('StudyInstanceUID', self.study_instance_uid)
        exp.setTag('SeriesInstanceUID', self.study_instance_uid + str(series_counter))
        file.dcm_series_instance_uid = self.study_instance_uid + str(series_counter)
        exp.setTag('FrameOfReferenceInstanceUID', self.study_instance_uid + str(series_counter) + str(series_counter))

        # StudyID
        exp.setTag('StudyID', self.study_instance_uid)

        # Modality
        # setting to US makes the files load as slices that are not recognised as one volume
        if "intra" in file.parent.name.lower() and "us" in file.parent.name.lower() and "us" in file.name.lower():
            exp.setTag('Modality', 'MR')  # todo this should be US, but for some reason loading US loads as slices
        elif "intra" in file.parent.name.lower() and "mr" in file.parent.name.lower() and "t" in file.name.lower():
            exp.setTag('Modality', 'MR')
        elif "pre" in file.parent.name.lower() and "imag" in file.parent.name.lower() and "t" in file.name.lower():
            exp.setTag('Modality', 'MR')
        elif "segment" in file.parent.name.lower():
            exp.setTag('Modality', 'SEG')  # we say that the segmentation is of the modality where it was created

        # SeriesDescription (name of the series in the hierarchy)
        exp.setTag('SeriesDescription', file.name)

        # SeriesNumber
        exp.setTag('SeriesNumber', series_counter)

    @staticmethod
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

    @staticmethod
    def convert_volume_to_segmentation(node, parent_node):
        """
        Function to convert a volume to a segmentation. First create a labelmap and then convert it to a segmentation.
        Also associates the segment node with the reference volume node (parent node)
        @param node: Name of the volume (node) in slicer which will be converted. Makes only sense for a binary
                            volume
        @param parent_node: Node of the parent of the segmentation
        @return: The segmentation node
        """
        # it is possible that it is already a segmentation, then just return it
        if "segmentationnode" in node.vtk_id.lower():
            return slicer.mrmlScene.GetNodeByID(node.vtk_id)

        # convert volume to label-map
        # create volume and label nodes
        volume_node = slicer.mrmlScene.GetNodeByID(node.vtk_id)
        label_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLabelMapVolumeNode')

        # create the label from the volume
        volumes_logic = slicer.modules.volumes.logic()
        volumes_logic.CreateLabelVolumeFromVolume(slicer.mrmlScene, label_node, volume_node)

        # create new empty segmentation and associate it with the right parent node
        segmentation_node = slicer.mrmlScene.AddNode(slicer.vtkMRMLSegmentationNode())
        # https://github.com/lassoan/LabelmapToDICOMSeg/blob/main/convert.py
        parent_volume_node = slicer.mrmlScene.GetNodeByID(parent_node.vtk_id)
        segmentation_node.SetNodeReferenceID(segmentation_node.GetReferenceImageGeometryReferenceRole(),
                                             parent_volume_node.GetID())

        # convert label-map to segmentation
        success = slicer.vtkSlicerSegmentationsModuleLogic.ImportLabelmapToSegmentationNode(label_node,
                                                                                            segmentation_node)

        # remove label map node
        slicer.mrmlScene.RemoveNode(label_node)

        if success:
            return segmentation_node
        else:
            return None

    def export_volumes_to_dicom(self):
        """
        Export volumes according to the created structure to DICOM

        UID has to be unique - that's how they get identified together
        """

        exporter_volumes = DICOMScalarVolumePlugin.DICOMScalarVolumePluginClass()

        bfs_array = Tree.bfs(self.folder_structure)

        counter = {}
        # loop through all nodes, but only use those that do not have children (volumes) and are not transforms
        for node in bfs_array:
            try:
                if not bool(node.children) \
                        and "transform" not in node.name.lower() \
                        and "annotation" not in node.parent.name.lower():
                    # only if it: does not have any children; is not a transformation; is not a segmentation
                    # increase/create counter for series number
                    if node.parent.name in counter:
                        counter[node.parent.name] += 1
                    else:
                        counter[node.parent.name] = 1

                    exportables = exporter_volumes.examineForExport(node.sh_id)

                    if not exportables:
                        raise ValueError("Nothing found to export. (Click 'Ok' to continue)")

                    # loop through exportables (should always be only one) and set dicom tags
                    for exp in exportables:
                        self.set_dicom_tags(exp, node, counter[node.parent.name])

                    exporter_volumes.export(exportables)

            except Exception as e:
                slicer.util.errorDisplay(f"Could not export node {node.name}. ({str(e)})")

    def import_reference_image(self, reference_dir_path):
        """
        Imports the reference dicom volume into the database
        :param reference_dir_path: Path to the folder with the reference volume
        """
        # save previous selected module
        previous_module = slicer.util.selectedModule()

        # check if dicom browser exists
        if slicer.modules.DICOMInstance.browserWidget is None:
            slicer.util.selectModule('DICOM')

        slicer.modules.DICOMInstance.browserWidget.dicomBrowser.importDirectory(reference_dir_path)
        slicer.modules.DICOMInstance.browserWidget.dicomBrowser.waitForImportFinished()

        # switch back to previous module
        slicer.util.selectModule(previous_module)

    def export_segmentations_to_dicom(self):
        """
        Exports segmentations
        """
        exporter_segmentation = DICOMSegmentationPlugin.DICOMSegmentationPluginClass()
        sh_node = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
        bfs_array = Tree.bfs(self.folder_structure)
        counter = {}

        # loop through all nodes, but only use those that do not have children (volumes) and are not transforms
        for node in bfs_array:
            try:
                if not bool(node.children) \
                        and "annotation" in node.parent.name.lower() \
                        and "landmark" not in node.name.lower():

                    # 1. load the reference dicom file into the database
                    # find parent of segmentation
                    parent = self.find_semantic_parent_of_a_segmentation(node.name, self.folder_structure, self.pre_op_name)

                    if parent is None:
                        slicer.util.errorDisplay(f"Could not export node {node.name}, couldn't find any parent.")
                        continue

                    parent_path = os.path.join(self.subject_folder, "ScalarVolume_" + str(parent.sh_id))

                    self.import_reference_image(parent_path)

                    loaded_volume_id = DICOMUtils.loadSeriesByUID([parent.dcm_series_instance_uid])
                    loaded_volume_node = slicer.mrmlScene.GetNodeByID(loaded_volume_id[0])

                    # 2. convert volume to segmentation
                    segmentation_node = self.convert_volume_to_segmentation(node, parent)

                    # 3. Change the parent in the subject hierarchy of the segmentation to the new loaded dicom
                    segmentation_id_in_hierarchy = sh_node.GetItemByDataNode(segmentation_node)
                    loaded_volume_id_in_hierarchy = sh_node.GetItemByDataNode(loaded_volume_node)
                    sh_node.SetItemParent(segmentation_id_in_hierarchy, loaded_volume_id_in_hierarchy)

                    # 4. In the segment editor change the reference geometry to the loaded volume
                    segmentation_node.SetReferenceImageGeometryParameterFromVolumeNode(loaded_volume_node)

                    # 5. export the segmentation
                    # increase/create counter for series number
                    if node.parent.name in counter:
                        counter[node.parent.name] += 1
                    else:
                        counter[node.parent.name] = 1

                    # todo how to change names
                    exportables = exporter_segmentation.examineForExport(segmentation_id_in_hierarchy)

                    for exp in exportables:
                        self.set_dicom_tags(exp, node, counter[node.parent.name])

                    exporter_segmentation.export(exportables)

            except Exception as e:
                slicer.util.errorDisplay(f"Could not export node {node.name}.\n({str(e)})\n"
                                         f"export_segmentations_to_dicom")

    def export_data(self):
        # 0. Clear DICOM database
        DICOMLib.clearDatabase(slicer.dicomDatabase)

        # 2. Create studies according to the folder structure
        self.create_studies_in_slicer()

        # 3. Export volumes according to the studies
        self.export_volumes_to_dicom()

        # 4. Export segmentations according to the studies
        self.export_segmentations_to_dicom()

        # 5. Export landmarks
        self.export_landmarks_to_json()

        # 5. Clear DICOM database
        DICOMLib.clearDatabase(slicer.dicomDatabase)


