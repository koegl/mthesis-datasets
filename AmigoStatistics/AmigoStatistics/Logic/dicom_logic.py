import slicer
import vtk
import DICOMScalarVolumePlugin

from Logic.tree import Tree

import os
import hashlib


class DicomLogic:
    """
    Class to encapsulate logic for exporting a scene to DICOM. Assumed structure:
    Scene
    └── Subject name/mrn
        ├── Pre-op imaging
        │   └── volumes
        ├── Intra-op imaging
        │   └── volumes
        ├── Segmentation
        │   └── lesion segmentation
        └── Annotations
            └── landmarks
    """
    # todo fix exporting with studies (already asked question on discourse)
    # todo figure out how to export segmentations
    # todo figure out how to export landmarks
    # todo figure out workflow for user interaction - probably user prepares the scene and then clicks a button

    def __init__(self, output_folder=None):

        if output_folder is None:
            self.output_folder = os.getcwd()
        else:
            self.output_folder = output_folder

        self.folder_structure = None

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

    def generate_folder_structure_as_tree(self):
        """
        Generate the folder structure as a tree
        """
        # 1. get item id of subject in hierarchy structure
        # we assume there is only one child
        child_ids_subject = vtk.vtkIdList()
        child_ids_folders = vtk.vtkIdList()
        child_ids_subfolders = vtk.vtkIdList()

        subject_hierarchy_node = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
        subject_hierarchy_node.GetItemChildren(subject_hierarchy_node.GetSceneItemID(), child_ids_subject)
        subject_item_id = child_ids_subject.GetId(0)

        self.folder_structure = Tree(subject_hierarchy_node.GetItemName(subject_item_id), id=subject_item_id)

        # 2. get item id's of folders
        subject_hierarchy_node.GetItemChildren(subject_item_id, child_ids_subject)
        for i in range(child_ids_subject.GetNumberOfIds()):
            folder_id = child_ids_subject.GetId(i)
            folder_name = subject_hierarchy_node.GetItemName(folder_id)
            self.folder_structure.add_child(Tree(folder_name, id=folder_id))

            # add children of folders
            subject_hierarchy_node.GetItemChildren(folder_id, child_ids_folders)
            for j in range(child_ids_folders.GetNumberOfIds()):
                file_id = child_ids_folders.GetId(j)
                file_name = subject_hierarchy_node.GetItemName(file_id)
                self.folder_structure.children[folder_name].add_child(Tree(file_name, id=file_id))

                # add sub-children
                subject_hierarchy_node.GetItemChildren(file_id, child_ids_subfolders)
                if child_ids_subfolders.GetNumberOfIds() > 0:
                    for k in range(child_ids_subfolders.GetNumberOfIds()):
                        sub_file_id = child_ids_subfolders.GetId(k)
                        sub_file_name = subject_hierarchy_node.GetItemName(sub_file_id)
                        self.folder_structure.children[folder_name].children[file_name].add_child(Tree(sub_file_name, id=sub_file_id))

    def create_studies_in_slicer(self):
        """
        Create studies according to the folder structure in Slicer
        """
        hierarchy_node = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)

        patient_item_id = self.folder_structure.id

        for child_name, child in self.folder_structure.children.items():
            # create the studies
            temp_study_id = hierarchy_node.CreateStudyItem(patient_item_id, child_name)

            # change parents form folders to studies
            for file_name, file in child.children.items():
                hierarchy_node.SetItemParent(file.id, temp_study_id)

    def generate_id(self, hash_string):
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

    def set_dicom_tags(self, exp, file):
        """
        Sets dicom tags of one exportable exp
        @param exp: The exportable
        @param file: The file in the hierarchy tree
        """

        # output folder
        exp.directory = self.output_folder

        # PatientID - get last element of subject name (MRN) and hash it - root name
        patient_id = self.generate_id(self.folder_structure.name)
        exp.setTag('PatientID', patient_id)

        # StudyDescription (name of the study in the hierarchy)
        # todo works only when hierarchy is not deeper than 2
        study_description = file.parent.name
        exp.setTag('StudyDescription', study_description)

        # StudyInstanceUID (unique for each study, series are grouped by this ID)
        study_instance_uid = self.generate_id(study_description)
        exp.setTag('StudyInstanceUID', study_instance_uid)

        # StudyID
        exp.setTag('StudyID', study_instance_uid)

        # Modality
        if "intra" in file.parent.name.lower() and "us" in file.name.lower():
            exp.setTag('Modality', 'US')
        else:
            exp.setTag('Modality', 'MR')

        # SeriesDescription (name of the series in the hierarchy)
        exp.setTag('SeriesDescription', file.name)

    def export_volumes_to_dicom(self):
        """
        Export volumes according to the created structure to DICOM

        UID has to be unique- - that's how they get identified together
        """

        exporter = DICOMScalarVolumePlugin.DICOMScalarVolumePluginClass()

        for folder_name, folder in self.folder_structure.children.items():
            for file_name, file in folder.children.items():
                exportables = exporter.examineForExport(file.id)

                if not exportables:
                    raise ValueError("Nothing found to export.")

                for exp in exportables:
                    self.set_dicom_tags(exp, file)

                # exporter.export(exportables)

    def full_export(self):
        """
        Perform all the steps to export
        """

        # 1. Generate folder structure
        self.generate_folder_structure_as_tree()

        # 2. Create studies according to the folder structure
        # self.create_studies_in_slicer()

        # 3. Export volumes according to the studies
        # self.export_volumes_to_dicom()
