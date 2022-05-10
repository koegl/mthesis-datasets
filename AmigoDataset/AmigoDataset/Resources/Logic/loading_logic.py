import slicer

import os


class LoadingLogic:
    """
    Class to encapuslate loading logic
    """

    def __init__(self):
        pass

    @staticmethod
    def load_annotation(annotation_path):

        if annotation_path.endswith(".json"):
            return slicer.util.loadMarkups(annotation_path)
        elif annotation_path.endswith(".nii"):
            # get fullname from annotation_path
            filename = os.path.basename(annotation_path)
            segmentation_name = filename.replace(".nii", "")

            labelmap_node = slicer.util.loadLabelVolume(annotation_path)
            segmentation_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode", segmentation_name)
            slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(labelmap_node, segmentation_node)
            segmentation_node.CreateClosedSurfaceRepresentation()

            slicer.mrmlScene.RemoveNode(labelmap_node)

            # turn of 2D slice-fill visibility
            segmentation_node.GetDisplayNode().SetAllSegmentsOpacity2DFill(False)

            # collapse segmentation folder structure
            subject_hierarchy_node = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
            segmentation_sh_id = subject_hierarchy_node.GetItemByName((segmentation_node.GetName()))

            subject_hierarchy_node.SetItemExpanded(segmentation_sh_id, False)

            return segmentation_node

        return None

    def load_structure(self):
        raise NotImplementedError("load_structure method is not implemented in the Parent class.")
