import slicer
import vtk
import DICOMScalarVolumePlugin
import DICOMSegmentationPlugin
from DICOMLib import DICOMUtils
import DICOMLib

from Resources.Logic.exporting_logic import ExportingLogic
from Resources.Logic.tree import Tree
from Resources.Logic.structure_logic import StructureLogic
from Resources.Logic.utils import collapse_segmentations

import os
# todo instead of reassigning stuff at random, make a function that reassigns everything based on the original structure
#      and it could compare with a 'new' structure and remove the difference
# todo there is another subject created with one study - when is it created? remvoe it
# todo fix for when segmentations have more than one parent


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

        self.subject_hierarchy = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)

        self.folder_structure = StructureLogic.bfs_generate_folder_structure_as_tree()
        self.folder_structure_original = StructureLogic.bfs_generate_folder_structure_as_tree()

    def clone_subject(self):
        """
        We want to work on a cloned version of the subject, so we can modify it without affecting the original
        @return: the cloned subject id
        """

        # create a new subject
        new_subject_id = self.subject_hierarchy.CreateSubjectItem(self.subject_hierarchy.GetSceneItemID(), self.folder_structure.name)

        # create a correspondence dict of old and new - we need this to assign reference geometries to the cloned segs
        correspondence_dict = {}

        # create folders
        for folder_name, folder in self.folder_structure.children.items():
            cloned_folder_id = self.subject_hierarchy.CreateFolderItem(self.subject_hierarchy.GetSceneItemID(), folder_name)
            self.subject_hierarchy.SetItemParent(cloned_folder_id, new_subject_id)

            for node_name, node in folder.children.items():
                cloned_node_id = slicer.modules.subjecthierarchy.logic().CloneSubjectHierarchyItem(self.subject_hierarchy, node.sh_id)
                cloned_node = self.subject_hierarchy.GetItemDataNode(cloned_node_id)

                correspondence_dict[node.vtk_id] = cloned_node.GetID()

                name = cloned_node.GetName()
                name = name.replace(' Copy', '')
                cloned_node.SetName(name)
                self.subject_hierarchy.SetItemParent(cloned_node_id, cloned_folder_id)

                if "segmentationnode" in node.vtk_id.lower():
                    # parent reference node
                    parent_reference_id = correspondence_dict[node.segmentation_reference_vtk_id]
                    parent_reference_node = slicer.mrmlScene.GetNodeByID(parent_reference_id)
                    cloned_node.SetReferenceImageGeometryParameterFromVolumeNode(parent_reference_node)

        self.folder_structure = StructureLogic.bfs_generate_folder_structure_as_tree()

        return new_subject_id

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

    def find_segmentation_parent_node(self, segmentation_node):
        bfs_array = Tree.bfs(self.folder_structure)

        segmentation_mrml_node = slicer.mrmlScene.GetNodeByID(segmentation_node.vtk_id)
        parent_vtk_id = segmentation_mrml_node.GetNodeReferenceID(slicer.vtkMRMLSegmentationNode.GetReferenceImageGeometryReferenceRole())

        # return the parent node of the segmentation
        for node in bfs_array:
            if node.vtk_id == parent_vtk_id:
                return node

        # if there is no parent reutrn the first pre-op node
        for node_name, node in self.folder_structure.children["Pre-op MR"].children.items():
            return node

        # if nothing is found return None
        return None

    def export_segmentations_to_dicom(self):
        exporter_segmentation = DICOMSegmentationPlugin.DICOMSegmentationPluginClass()

        counter = {}

        bfs_array = Tree.bfs(self.folder_structure)

        for node in bfs_array:

            # volumes and segmentations
            if "segmentationnode" in node.vtk_id.lower():
                # increase/create counter for series number
                if node.parent.name in counter:
                    counter[node.parent.name] += 1
                else:
                    counter[node.parent.name] = 1

                # load segmentation parent/reference image from DICOM
                parent_node = self.find_segmentation_parent_node(node)

                if parent_node is None:
                    slicer.util.errorDisplay(f"Could not export node {node.name}, couldn't find any parent.")
                    continue

                # load the parent volume
                parent_path = os.path.join(self.subject_folder, "ScalarVolume_" + str(parent_node.sh_id))
                self.import_reference_image(parent_path)

                loaded_volume_id = DICOMUtils.loadSeriesByUID([parent_node.dcm_series_instance_uid])
                loaded_volume_node = slicer.mrmlScene.GetNodeByID(loaded_volume_id[0])

                segmentation_node = slicer.mrmlScene.GetNodeByID(node.vtk_id)
                original_reference_id = segmentation_node.GetNodeReferenceID(slicer.vtkMRMLSegmentationNode.GetReferenceImageGeometryReferenceRole())
                original_reference_node = slicer.mrmlScene.GetNodeByID(original_reference_id)
                segmentation_node.SetReferenceImageGeometryParameterFromVolumeNode(loaded_volume_node)

                # define the exportables
                exportables = exporter_segmentation.examineForExport(node.sh_id)

                if not exportables or not exporter_segmentation:
                    raise ValueError("Nothing found to export. (Click 'Ok' to continue)")

                # loop through exportables (should always be only one) and set dicom tags
                for exp in exportables:
                    self.set_dicom_tags(exp, node, counter[node.parent.name])

                exporter_segmentation.export(exportables)

                # set the original node back to the segmentation as reference
                segmentation_node.SetReferenceImageGeometryParameterFromVolumeNode(original_reference_node)

                # remove the loaded volume
                slicer.mrmlScene.RemoveNode(loaded_volume_node)

        # set the original node back to the correct folder
        for temp_node_name, temp_node in self.folder_structure_original.children["Annotations"].children.items():
            if "segmentationnode" in temp_node.vtk_id.lower():
                first_seg_node = temp_node
                break

        original_reference_vtk_id = first_seg_node.segmentation_reference_vtk_id
        original_reference_tree_node = self.folder_structure_original.find_node_by_vtk_id(original_reference_vtk_id)
        preo_op_node = self.folder_structure_original.children["Pre-op MR"]

        self.subject_hierarchy.SetItemParent(original_reference_tree_node.sh_id, preo_op_node.sh_id)

    def export_volumes_to_dicom(self):
        exporter_volumes = DICOMScalarVolumePlugin.DICOMScalarVolumePluginClass()

        counter = {}

        bfs_array = Tree.bfs(self.folder_structure)

        for node in bfs_array:

            # volumes and segmentations
            if "scalarvolumenode" in node.vtk_id.lower():
                # increase/create counter for series number
                if node.parent.name in counter:
                    counter[node.parent.name] += 1
                else:
                    counter[node.parent.name] = 1

                # define the exportables
                exportables = exporter_volumes.examineForExport(node.sh_id)

                if not exportables or not exporter_volumes:
                    raise ValueError("Nothing found to export. (Click 'Ok' to continue)")

                # loop through exportables (should always be only one) and set dicom tags
                for exp in exportables:
                    self.set_dicom_tags(exp, node, counter[node.parent.name])

                exporter_volumes.export(exportables)

    def remove_left_over_patients(self):
        patient_ids = vtk.vtkIdList()
        self.subject_hierarchy.GetItemChildren(self.subject_hierarchy.GetSceneItemID(), patient_ids)

        for i in range(1, patient_ids.GetNumberOfIds()):
            self.subject_hierarchy.RemoveItem(patient_ids.GetId(i))

    def remove_left_over_studies(self):
        buf_structure = StructureLogic.bfs_generate_folder_structure_as_tree()
        all_nodes = Tree.bfs(buf_structure)

        for node in all_nodes:
            if '(' in node.name or ')' in node.name:
                self.subject_hierarchy.RemoveItem(node.sh_id)

    def export_data(self):

        # clone subject
        cloned_subject_id = self.clone_subject()

        # 0. Clear DICOM database
        DICOMLib.clearDatabase(slicer.dicomDatabase)

        # 2. Create studies according to the folder structure
        self.create_studies_in_slicer()

        # 3. Export volumes according to the studies
        self.export_volumes_to_dicom()

        # 4. Export segmentations according to the studies
        self.export_segmentations_to_dicom()

        # 5. Export landmarks
        self.export_landmarks_to_json(self.subject_folder)

        # 5. Clear DICOM database
        DICOMLib.clearDatabase(slicer.dicomDatabase)

        # delete cloned subject
        self.remove_left_over_patients()
        self.remove_left_over_studies()

        # collapse segmentations
        collapse_segmentations(self.folder_structure, self.subject_hierarchy)