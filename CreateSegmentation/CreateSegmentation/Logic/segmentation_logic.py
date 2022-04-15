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

    def __init__(self):
        pass
