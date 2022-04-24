import vtk
import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

from AdditionalLogic.nifti_exporting_logic import NiftiExportingLogic
from AdditionalLogic.structure_logic import StructureLogic
from AdditionalLogic.statistics_exporting_logic import StatisticsExportingLogic

import os
try:
    from tqdm import tqdm
except ImportError:
    slicer.util.pip_install('tqdm')
    from tqdm import tqdm


#
# AmigoDataset
#

class AmigoDataset(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "AmigoDataset"
        self.parent.categories = ["Informatics"]
        self.parent.dependencies = ["Markups"]
        self.parent.contributors = ["Fryderyk Kögl (TUM, BWH)"]
        self.parent.helpText = """
    Module that gather useful Slicer functionality for setting landmarks in MR and US images. To start choose the
    volumes that you want to use, create an intersection of the US FOV to make sure your landmarks are all in an
    overlapping area and the customise your view. Use the shortcuts listed at the bottom to increase the efficiency of
    the workflow.
    https://github.com/koegl/NiftiExport
    """
        self.parent.acknowledgementText = """
    This extension was developed at the Brigham and Women's Hospital by Fryderyk Kögl, Harneet Cheema and Tina Kapur.

    This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
    and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
    """


#
# NiftiExportWidget
#
class AmigoDatasetWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

    def __init__(self, parent=None):
        """
    Called when the user opens the module the first time and the widget is initialized.
    """
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._updatingGUIFromParameterNode = False

        self.deidentify = False
        self.identity = False
        self.parent_identity = ""
        self.resample = False
        self.resample_spacing = None

    def setup(self):
        """
    Called when the user opens the module the first time and the widget is initialized.
    """
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath('UI/AmigoDataset.ui'))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. AdditionalLogic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = AmigoDatasetLogic()

        # Connections
        self.ui.deidentifyCheckBox.connect('clicked(bool)', self.onDeidentifyCheckBox)
        self.ui.identityCheckBox.connect('clicked(bool)', self.onIdentityCheckBox)
        self.ui.resampleCheckbox.connect('clicked(bool)', self.onResampleCheckBox)

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
        # (in the selected parameter node).

        # Buttons
        self.ui.exportCurrentSceneToNiftiButton.connect('clicked(bool)', self.onExportCurrentSceneToNiftiButton)
        self.ui.exportAllMrbsFoundInFolderToNiftiButton.connect('clicked(bool)',
                                                                self.onExportAllMrbsFoundInFolderToNiftiButton)
        self.ui.loadFolderStructureButton.connect('clicked(bool)', self.onLoadFolderStructureButton)
        self.ui.exportCurrentSceneStatisticsButton.connect('clicked(bool)', self.onExportCurrentSceneStatisticsButton)
        self.ui.exportAllMRBStatisticsButton.connect('clicked(bool)', self.onExportAllMRBStatisticsButton)

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

    def cleanup(self):
        """
    Called when the application closes and the module widget is destroyed.
    """
        self.removeObservers()

    def enter(self):
        """
    Called each time the user opens this module.
    """
        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def exit(self):
        """
    Called each time the user opens a different module.
    """
        # Do not react to parameter node changes (GUI wlil be updated when the user enters into the module)
        self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

    def onSceneStartClose(self, caller, event):
        """
    Called just before the scene is closed.
    """
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event):
        """
    Called just after the scene is closed.
    """
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self):
        """
    Ensure parameter node exists and observed.
    """
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())

    def setParameterNode(self, inputParameterNode):
        """
    Set and observe parameter node.
    Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
    """

        # Unobserve previously selected parameter node and add an observer to the newly selected.
        # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
        # those are reflected immediately in the GUI.
        if self._parameterNode is not None:
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
        self._parameterNode = inputParameterNode
        if self._parameterNode is not None:
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

        # Initial GUI update
        self.updateGUIFromParameterNode()

    def updateGUIFromParameterNode(self, caller=None, event=None):
        """
    This method is called whenever parameter node is changed.
    The module GUI is updated to show the current state of the parameter node.
    """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
        self._updatingGUIFromParameterNode = True

        # All the GUI updates are done
        self._updatingGUIFromParameterNode = False

    def updateParameterNodeFromGUI(self, caller=None, event=None):
        """
    This method is called when the user makes any change in the GUI.
    The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
    """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

        self._parameterNode.EndModify(wasModified)

    def onIdentityCheckBox(self, activate=False):
        self.identity = activate

        # enable mainIdentityText if identity is activated
        if self.identity:
            self.ui.mainIdentityText.enabled = True
        else:
            self.ui.mainIdentityText.enabled = False

    def onDeidentifyCheckBox(self, activate=False):
        self.deidentify = activate

    def onResampleCheckBox(self, activate=False):
        self.resample = activate

        # enable resampleText if resample is activated
        if self.resample:
            self.ui.resampleText.enabled = True
        else:
            self.ui.resampleText.enabled = False

    def onExportCurrentSceneToNiftiButton(self):
        """
        Exports the current scene (according to the hierarchy) to nifti. Assumed structure:
        """
        try:
            print("\n\nExporting current scene to Nifti...\n")

            # get the nifti output folder path
            nifti_output_folder_path = self.ui.niftiOutputPathTextWindow.toPlainText()

            if not os.path.isdir(nifti_output_folder_path):
                raise NotADirectoryError("The nifti output folder path does not exist.")

            # Create NiftiExportLogic
            nifti_logic = NiftiExportingLogic(output_folder=nifti_output_folder_path,
                                              deidentify=self.deidentify)

            # export to nifti
            if self.identity is True:
                self.parent_identity = self.ui.mainIdentityText.toPlainText()
            if self.resample is True:
                self.resample_spacing = float(self.ui.resampleText.toPlainText())
            nifti_logic.full_export(self.parent_identity, self.resample_spacing)

            print("\nFinished exporting to Nifti.")

        except Exception as e:
            slicer.util.errorDisplay("Couldn't export current scene to Nifti.\n{}".format(e),
                                     windowTitle="Export error")

    def onExportAllMrbsFoundInFolderToNiftiButton(self):
        """
        Export all mrb's found in the folder to nifti
        """
        # todo add check to see which mrbs could and which could not be exported

        try:
            print("\n\nExporting all mrbs found in the folder to Nifti...\n")

            # Get the folder path from the GUI
            folder_path = self.ui.mrbFolderPathTextWindow.toPlainText()

            # extract all mrbs from the folder
            mrb_paths_list = StructureLogic.return_a_list_of_all_mrbs_in_a_folder(folder_path)

            # get the nifti output folder path
            nifti_output_folder_path = self.ui.niftiOutputPathTextWindow.toPlainText()

            if not os.path.isdir(nifti_output_folder_path):
                raise NotADirectoryError("The nifti output folder path does not exist.")

            # check if the path is valid
            if not os.path.isdir(nifti_output_folder_path):
                raise Exception("The nifti output path is not valid.")

            # export all to nifti
            # Create NiftiExportLogic
            nifti_logic = NiftiExportingLogic(output_folder=nifti_output_folder_path, deidentify=self.deidentify)

            for i in tqdm(range(len(mrb_paths_list)), "Exporting current scene to Nifti"):
                mrb_path = mrb_paths_list[i]

                # clear scene at the beginning of each mrb in case older data is still present
                slicer.mrmlScene.Clear()

                try:
                    # open mrb to slicer scene
                    try:
                        slicer.util.loadScene(mrb_path)
                    except Exception as e:  # needs to be this broad because slicer.util.loadScene can throw an exception
                        # that does not impact the process except for interrupting and requiring user input
                        pass

                    # export current scene to nifti
                    nifti_logic.full_export()

                    # clear scene
                    slicer.mrmlScene.Clear()
                except Exception as e:
                    print(f"Could not export {mrb_path} to Nifti.\n{e}")

            print("\nFinished exporting all mrbs found in the folder to Nifti.")

        except Exception as e:
            slicer.util.errorDisplay("Couldn't export mrbs to Nifti.\n{}".format(e), windowTitle="Export error")

    def onLoadFolderStructureButton(self):

        try:
            folder_structure_path = self.ui.folderStructurePathTextWindow.toPlainText()

            # load folder structure
            folders = []
            buf = os.listdir(folder_structure_path)
            for folder in buf:
                if "store" not in folder.lower() and os.path.isdir(os.path.join(folder_structure_path, folder)):
                    folders.append(folder)

            # get .json landmark file path
            landmark_file_path = ""
            for folder in buf:
                temp = os.path.join(folder_structure_path, folder)
                if temp.endswith(".json"):
                    landmark_file_path = temp
                    break

            hierarchy_node = slicer.mrmlScene.GetSubjectHierarchyNode()

            # create patient
            # get last folder name from folder_structure_path
            subject_folder_id = os.path.basename(os.path.normpath(folder_structure_path))
            patient_id = hierarchy_node.CreateSubjectItem(hierarchy_node.GetSceneItemID(), subject_folder_id)

            # load landmark file
            if landmark_file_path is not None:
                markups_node = slicer.util.loadMarkups(landmark_file_path)
                markups_hierarchy_id = hierarchy_node.GetItemByDataNode(markups_node)
                hierarchy_node.SetItemParent(markups_hierarchy_id, patient_id)

            # create folder structure and load nifti files into it
            for data_folder in folders:
                data_folder_id = hierarchy_node.CreateFolderItem(hierarchy_node.GetSceneItemID(), data_folder)
                hierarchy_node.SetItemParent(data_folder_id, patient_id)
                data_folder_path = os.path.join(folder_structure_path, data_folder)

                # for all nifti files in the folder
                for root, dirs, files in os.walk(data_folder_path):
                    for file in files:
                        if file.endswith(".nii"):
                            temp_path = os.path.join(root, file)
                            temp_volume_node = slicer.util.loadVolume(temp_path)
                            temp_volume_hierarchy_id = hierarchy_node.GetItemByDataNode(temp_volume_node)
                            hierarchy_node.SetItemParent(temp_volume_hierarchy_id, data_folder_id)

        except Exception as e:
            slicer.util.errorDisplay("Couldn't load folder structure.\n{}".format(e), windowTitle="Load error")

    def onExportCurrentSceneStatisticsButton(self):
        statistics_exporter = StatisticsExportingLogic()
        statistics_exporter.export_current_scene()

    def onExportAllMRBStatisticsButton(self):
        try:
            mrb_paths = self.ui.mrbStatisticsInputTextWindow.toPlainText()
            statistics_exporter = StatisticsExportingLogic()
            statistics_exporter.export_multiple_scenes(mrb_paths=mrb_paths)
        except Exception as e:
            slicer.util.errorDisplay("Couldn't export mrb statistics.\n{}".format(e), windowTitle="Statistics export error")

#
# AmigoDatasetLogic
#

class AmigoDatasetLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

    def __init__(self):
        """
    Called when the logic class is instantiated. Can be used for initializing member variables.
    """
        ScriptedLoadableModuleLogic.__init__(self)


#
# AmigoDatasetTest
#
#
class AmigoDatasetTest(ScriptedLoadableModuleTest):
    """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here.
    """
        self.setUp()
        self.test_AmigoDataset1()

    def test_AmigoDataset1(self):
        """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

        self.delayDisplay("Starting the test")

        logic = AmigoDatasetLogic()

        pass

        self.delayDisplay('Test passed')

