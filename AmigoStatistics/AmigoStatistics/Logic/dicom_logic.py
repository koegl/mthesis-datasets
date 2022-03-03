import slicer
import vtk
import DICOMScalarVolumePlugin
import DICOMSegmentationPlugin

from Logic.tree import Tree

import os
import hashlib
import numpy as np
import logging


class DicomLogic:
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
    # todo figure out how to export segmentations
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
            child.study_id = hierarchy_node.CreateStudyItem(self.folder_structure.id, child.name)
            hierarchy_node.SetItemParent(child.study_id, self.folder_structure.id)

        # loop through all nodes in BFS order
        bfs_array_of_nodes = Tree.bfs(self.folder_structure)
        for node in bfs_array_of_nodes:
            if node.study_id is None:  # true if the node is not a study -> a series
                hierarchy_node.SetItemParent(node.id, node.parent.study_id)

    def harden_transformations(self):
        """
        Hardens all transformations
        """

        all_nodes = Tree.bfs(self.folder_structure)

        for node in all_nodes:
            # harden transformation
            buf_node = slicer.util.getFirstNodeByName(node.name)

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

    def set_dicom_tags(self, exp, file, series_counter=None):
        """
        Sets dicom tags of one exportable exp
        @param exp: The exportable
        @param file: The file in the hierarchy tree
        @param series_counter: Counts at which series we currently are
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

        # StudyInstanceUID (unique for each study, series are grouped by this ID)
        study_instance_uid = self.generate_id(study_description + self.folder_structure.name)
        exp.setTag('StudyInstanceUID', study_instance_uid)

        # StudyID
        exp.setTag('StudyID', study_instance_uid)

        # Modality
        # setting to US makes the files load as slices that are not recognised as one volume
        if "intra" in file.parent.name.lower() and "us" in file.parent.name.lower() and "us" in file.name.lower():
            exp.setTag('Modality', 'MR')
        elif "intra" in file.parent.name.lower() and "mr" in file.parent.name.lower() and "t" in file.name.lower():
            exp.setTag('Modality', 'MR')
        elif "pre" in file.parent.name.lower() and "imag" in file.parent.name.lower() and "t" in file.name.lower():
            exp.setTag('Modality', 'MR')
        # elif "segment" in file.parent.name.lower():
            # exp.setTag('Modality', 'MR')  # we say that the segmentation is of the modality where it was created

        # SeriesDescription (name of the series in the hierarchy)
        exp.setTag('SeriesDescription', file.name)

        # SeriesNumber
        if series_counter:
            exp.setTag('SeriesNumber', series_counter)

    @staticmethod
    # todo how to set the right parent of the segmentation
    def convert_volume_to_segmentation(volume_name):
        """
        Function to convert a volume to a segmentation. First create a labelmap and then convert it to a segmentation.
        Also associates the segment node with the reference volume node
        @param volume_name: Name of the volume (node) in slicer which will be converted. Makes only sense for a binary
                            volume
        @return: The segmentation node
        """

        # convert volume to label-map
        volume_node = slicer.util.getFirstNodeByName(volume_name)
        volume_data = slicer.util.arrayFromVolume(volume_node)
        volume_data = volume_data.astype(np.uint8())

        label_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLabelMapVolumeNode')

        # place np array in label node
        slicer.util.updateVolumeFromArray(label_node, volume_data)

        # fix orientation of label_node
        volume_matrix = vtk.vtkMatrix4x4()
        volume_node.GetIJKToRASMatrix(volume_matrix)
        volume_origin = volume_node.GetOrigin()
        label_node.SetIJKToRASMatrix(volume_matrix)
        label_node.SetOrigin(volume_origin)

        # create new empty segmentation
        segmentation_node = slicer.mrmlScene.AddNode(slicer.vtkMRMLSegmentationNode())

        # convert label-map to segmentation
        success = slicer.vtkSlicerSegmentationsModuleLogic.ImportLabelmapToSegmentationNode(label_node, segmentation_node)

        # associate segmentation node with a reference volume node (input node)
        sh_node = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
        volume_id_in_hierarchy = sh_node.GetItemByDataNode(volume_node)
        study_item_id = sh_node.GetItemParent(volume_id_in_hierarchy)
        segmentation_id_in_hierarchy = sh_node.GetItemByDataNode(segmentation_node)
        # todo check if this is necessary
        sh_node.SetItemParent(segmentation_id_in_hierarchy, study_item_id)

        if success:
            return sh_node.GetItemByDataNode(segmentation_node)
        else:
            return None

    def export_volumes_to_dicom(self):
        """
        Export volumes according to the created structure to DICOM

        UID has to be unique- - that's how they get identified together
        """

        exporter_volumes = DICOMScalarVolumePlugin.DICOMScalarVolumePluginClass()
        exporter_segmentation = DICOMSegmentationPlugin.DICOMSegmentationPluginClass()

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

                if not bool(node.children) and "transform" not in node.name.lower() and "segment" in node.parent.name.lower():
                    # only if it: does not have any children; is not a transformation; is a segmentation

                    # increase/create counter for series number
                    if node.parent.name in counter:
                        counter[node.parent.name] += 1
                    else:
                        counter[node.parent.name] = 1

                    # convert volume to segmentation
                    segmentation_node_id_buf = self.convert_volume_to_segmentation(node.name)
                    exportables = exporter_segmentation.examineForExport(segmentation_node_id_buf)

                    for exp in exportables:
                        pass #self.set_dicom_tags(exp, node, counter[node.parent.name])

                    # exporter_segmentation.export(exportables)
            except Exception as e:
                print(f"\n\nCould not export node: {node.name}.\n{str(e)}\n\n")

    def full_export(self):
        """
        Perform all the steps to export
        """

        # 1. Generate folder structure
        self.bfs_generate_folder_structure_as_tree()

        # 2. Create studies according to the folder structure
        self.create_studies_in_slicer()

        # 3. Harden transforms
        self.harden_transformations()

        # 3. Export volumes according to the studies
        self.export_volumes_to_dicom()