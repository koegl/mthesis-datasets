import slicer
import vtk
import qt
import DICOMScalarVolumePlugin
import DICOMSegmentationPlugin
from DICOMLib import DICOMUtils
import DICOMLib

from Logic.tree import Tree

import os
import hashlib
import logging


class DicomExportLogic:
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
        └── Annotations
            └── landmarks
    """
    # todo figure out how to export landmarks
    # todo figure out workflow for user interaction - probably user prepares the scene and then clicks a button

    def __init__(self, output_folder=None, log_path="/Users/fryderykkogl/Desktop/log.log"):

        if output_folder is None:
            self.output_folder = os.getcwd()
        else:
            self.output_folder = output_folder

        self.folder_structure = None

        logging.basicConfig(filename=log_path)
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)  # lowest level from ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')

    def bfs_generate_folder_structure_as_tree(self):
        """
        Generate the folder structure as a tree
        """
        # create a list with children and get the subject node
        child_ids = vtk.vtkIdList()
        subject_hierarchy_node = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
        subject_hierarchy_node.GetItemChildren(subject_hierarchy_node.GetSceneItemID(), child_ids)
        id = child_ids.GetId(0)

        # FIFO queue of nodes and create root
        self.folder_structure = Tree(subject_hierarchy_node.GetItemName(id), id=id)
        visited = [id]  # array to store visited IDs
        nodes_queue = [self.folder_structure]

        while nodes_queue:
            # dequeue node
            s = nodes_queue.pop(0)

            # get all children of the dequeued node s and add to queue if not visited
            subject_hierarchy_node.GetItemChildren(s.id, child_ids)

            for i in range(child_ids.GetNumberOfIds()):
                sub_id = child_ids.GetId(i)
                if sub_id not in visited:
                    sub_name = subject_hierarchy_node.GetItemName(sub_id)
                    sub_child = s.add_child(Tree(sub_name, id=sub_id))  # this returns the node which is like a C++
                    # reference, so we can use this in the next iteration to append nodes
                    nodes_queue.append(sub_child)
                    visited.append(sub_id)

    def create_studies_in_slicer(self):
        """
        Create studies according to the folder structure in Slicer
        """
        hierarchy_node = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)

        # create studies
        for _, child in self.folder_structure.children.items():
            if 'transform' in child.name.lower():  # we don't want to create a study for the transform
                continue
            child.study_id = hierarchy_node.CreateStudyItem(self.folder_structure.id, child.name)
            hierarchy_node.SetItemParent(child.study_id, self.folder_structure.id)

        # loop through all nodes in BFS order
        bfs_array_of_nodes = Tree.bfs(self.folder_structure)
        for node in bfs_array_of_nodes:
            if node.study_id is None and 'transform' not in node.name.lower():  # true if the node is not a study -> a series
                hierarchy_node.SetItemParent(node.id, node.parent.study_id)

    def harden_transformations(self):
        """
        Hardens all transformations
        """

        all_nodes = Tree.bfs(self.folder_structure)

        for node in all_nodes:
            # harden transformation
            buf_node = slicer.mrmlScene.GetFirstNode(node.name)

            if buf_node:  # if it exists
                buf_node.HardenTransform()

    @staticmethod
    def generate_id(hash_string):
        """
        Generates a unique id by hashing hash_string. (unique up to 999999999)
        @param hash_string: The path which will be hashed
        @return: the id
        """

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

    def set_dicom_tags(self, exp, file, series_counter=1, segmentation=None):
        """
        Sets dicom tags of one exportable exp
        @param exp: The exportable
        @param file: The file in the hierarchy tree
        @param series_counter: Counts at which series we currently are
        @param segmentation: A node with a parent - only available if we have a segmentation
        """

        # output folder
        exp.directory = self.output_folder

        # PatientID - get last element of subject name (MRN) and hash it - root name
        patient_id = self.generate_id(self.folder_structure.name)
        exp.setTag('PatientID', patient_id)
        exp.setTag('PatientName', patient_id)

        # StudyDescription (name of the study in the hierarchy)
        study_description = file.parent.name
        exp.setTag('StudyDescription', study_description)

        # If any of UIDs (studyInstanceUID, seriesInstanceUID, and frameOfReferenceInstanceUID) are specified then all
        # of them must be specified.
        # StudyInstanceUID (unique for each study, series are grouped by this ID)
        study_instance_uid = self.generate_id(study_description + self.folder_structure.name)
        exp.setTag('StudyInstanceUID', study_instance_uid)
        exp.setTag('SeriesInstanceUID', study_instance_uid + str(series_counter))
        file.series_instance_uid = study_instance_uid + str(series_counter)
        exp.setTag('FrameOfReferenceInstanceUID', study_instance_uid + str(series_counter) + str(series_counter))

        # StudyID
        exp.setTag('StudyID', study_instance_uid)

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

    def find_semantic_parent_of_a_segmentation(self, segmentation_name):
        """
        Function to find the semantic parent of a segmentation - semantic referring to the fact that we are not looking
        at the hierarchy tree, as the segmentaion will be in a different folder. What we are doing instead is only look
        at the pre-operative imaging (that's where the lesions were created) and find the volume which corresponds to
        the segmentation
        @param segmentation_name: The name of the segmentation
        @return: The volume node of the parent
        """

        # split segmentation_name into sub-words that can be searched for in the potential parent
        segmentation_name_split = segmentation_name.split(" ")

        # loop through pre-op imaging nodes
        for preop_name, preop_node in self.folder_structure.children['Pre-op Imaging'].children.items():

            # check if any of the sub-words of the segmentation appear in the node name - only T1
            if "t1" in preop_name.lower():
                return preop_node

        # if nothing was found, return None
        return None

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

        # convert volume to label-map
        # create volume and label nodes
        volume_node = slicer.mrmlScene.GetFirstNode(node.name)
        label_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLabelMapVolumeNode')

        # create the label from the volume
        volumes_logic = slicer.modules.volumes.logic()
        volumes_logic.CreateLabelVolumeFromVolume(slicer.mrmlScene, label_node, volume_node)

        # create new empty segmentation and associate it with the right parent node
        segmentation_node = slicer.mrmlScene.AddNode(slicer.vtkMRMLSegmentationNode())
        # https://github.com/lassoan/LabelmapToDICOMSeg/blob/main/convert.py
        parent_volume_node = slicer.mrmlScene.GetFirstNode(parent_node.name)
        segmentation_node.SetNodeReferenceID(segmentation_node.GetReferenceImageGeometryReferenceRole(),
                                             parent_volume_node.GetID())

        # convert label-map to segmentation
        success = slicer.vtkSlicerSegmentationsModuleLogic.ImportLabelmapToSegmentationNode(label_node, segmentation_node)

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
                if not bool(node.children) and "transform" not in node.name.lower() and "segment" not in node.parent.name.lower():
                    # only if it: does not have any children; is not a transformation; is not a segmentation

                    # increase/create counter for series number
                    if node.parent.name in counter:
                        counter[node.parent.name] += 1
                    else:
                        counter[node.parent.name] = 1

                    exportables = exporter_volumes.examineForExport(node.id)

                    if not exportables:
                        raise ValueError("Nothing found to export.")

                    # loop through exportables (should always be only one) and set dicom tags
                    for exp in exportables:
                        self.set_dicom_tags(exp, node, counter[node.parent.name])

                    exporter_volumes.export(exportables)

            except Exception as e:
                self.logger.log(logging.ERROR, f"Could not export node {node.name}. ({str(e)})")

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
                if not bool(node.children) and\
                        "transform" not in node.name.lower()\
                        and "segment" in node.parent.name.lower():

                    # 1. load the reference dicom file into the database
                    # find parent of segmentation
                    parent = self.find_semantic_parent_of_a_segmentation(node.name)

                    if parent is None:
                        self.logger.log(logging.ERROR, f"Could not export node {node.name}, couldn't find any parent.")
                        continue

                    parent_path = os.path.join(self.output_folder, "ScalarVolume_" + str(parent.id))

                    self.import_reference_image(parent_path)

                    loaded_volume_id = DICOMUtils.loadSeriesByUID([parent.series_instance_uid])
                    loaded_volume_node = slicer.util.getNode(loaded_volume_id[0])

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
                self.logger.log(logging.ERROR, f"Could not export node {node.name}.\n({str(e)})\n"
                                               f"export_segmentations_to_dicom")

    def full_export(self):
        """
        Perform all the steps to export
        """

        # 0. Clear DICOM database
        DICOMLib.clearDatabase(slicer.dicomDatabase)

        # 1. Generate folder structure
        self.bfs_generate_folder_structure_as_tree()

        # 2. Create studies according to the folder structure
        self.create_studies_in_slicer()

        # 3. Harden transforms
        self.harden_transformations()

        # 3. Export volumes according to the studies
        self.export_volumes_to_dicom()

        # 4. Export segmentations according to the studies
        self.export_segmentations_to_dicom()

        # 5. Clear DICOM database
        DICOMLib.clearDatabase(slicer.dicomDatabase)
