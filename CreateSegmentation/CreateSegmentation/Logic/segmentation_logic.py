import slicer
import vtk
import qt
import DICOMScalarVolumePlugin
import DICOMSegmentationPlugin
from DICOMLib import DICOMUtils
import DICOMLib

import os


class SegmentationLogic:
    """
    This class is used to convert a volume in slicer to a segmentation
    """

    def __init__(self, segmentation_name, parent_name):
        self.segmentation_volume_name = segmentation_name
        self.parent_name = parent_name

        if not slicer.util.getFirstNodeByName(self.segmentation_volume_name):
            slicer.util.errorDisplay("No segmentation volume found with this name")
        else:
            self.segmentation_volume_node = slicer.util.getFirstNodeByName(self.segmentation_volume_name)

        if not slicer.util.getFirstNodeByName(self.parent_name):
            slicer.util.errorDisplay("No parent volume found with this name")
        else:
            self.parent_node = slicer.util.getFirstNodeByName(self.parent_name)

        self.segmentation_vtk_id = self.segmentation_volume_node.GetID()
        self.parent_vtk_id = self.parent_node.GetID()

    def setup_segment_editor(self, segmentation_node=None, volume_node=None):
        """
        Runs standard setup of segment editor widget and segment editor node
        :param segmentation_node a seg node you can also pass
        :param volume_node a volume node you can pass
        """

        if segmentation_node is None:
            # Create segmentation node
            segmentation_node = slicer.vtkMRMLSegmentationNode()
            segmentation_node.SetName(self.segmentation_volume_name)
            slicer.mrmlScene.AddNode(segmentation_node)
            segmentation_node.CreateDefaultDisplayNodes()

        segment_editor_widget = slicer.qMRMLSegmentEditorWidget()
        segment_editor_node = slicer.vtkMRMLSegmentEditorNode()
        segment_editor_node.SetOverwriteMode(slicer.vtkMRMLSegmentEditorNode.OverwriteNone)
        slicer.mrmlScene.AddNode(segment_editor_node)
        segment_editor_widget.setMRMLSegmentEditorNode(segment_editor_node)
        segment_editor_widget.setSegmentationNode(segmentation_node)
        segment_editor_widget.setMRMLScene(slicer.mrmlScene)

        if volume_node:
            segment_editor_widget.setMasterVolumeNode(volume_node)

        return segment_editor_widget, segment_editor_node, segmentation_node

    def create_segmentation(self):
        """
        Creates a segmentation object from a volume (binary) and assigns it to the correct parent
        """

        # initialise segment editor
        segment_editor_widget, segment_editor_node, segmentation_node = self.setup_segment_editor()

        # create a threshold segmentation
        segment_editor_widget.setMasterVolumeNode(self.segmentation_volume_node)

        # create segment
        segment_id = segmentation_node.GetSegmentation().AddEmptySegment()
        segment_editor_node.SetSelectedSegmentID(segment_id)

        # Fill by thresholding
        segment_editor_widget.setActiveEffectByName("Threshold")
        effect = segment_editor_widget.activeEffect()
        effect.setParameter("MinimumThreshold", "1")
        effect.setParameter("MaximumThreshold", "255")
        effect.self().onApply()

        # display only outline
        segmentation_node = slicer.mrmlScene.GetNodeByID(segmentation_node.GetID())
        display_node = segmentation_node.GetDisplayNode()
        display_node.SetSegmentOpacity2DFill(segment_id, 0.0)  # Set fill opacity of a single segment
        display_node.SetSegmentOpacity2DOutline(segment_id, 1.0)  # Set outline opacity of a single segment

        # set correct parent
        segmentation_node.SetReferenceImageGeometryParameterFromVolumeNode(self.parent_node)

        # remove volume node that contained the segmentation
        slicer.mrmlScene.RemoveNode(self.segmentation_volume_node)
