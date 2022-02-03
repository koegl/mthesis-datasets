import Resources.Logic.xlsx_exporting_logic as xlsx_exporting_logic
import Resources.Logic.json_dict_logic as json_dict_logic

import vtk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import os
from os.path import exists
import json
from os import listdir
from os.path import isfile, join

try:
    import pandas as pd
except:
    slicer.util.pip_install('library_name')
    import pandas as pd
slicer.util.pip_install('xlsxwriter')

# TODO ADD A TEXT FIELD FOR ALL THE PATHS - were to save the .jsons etc



#
# AmigoStatistics
#

class AmigoStatistics(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "AmigoStatistics"
    self.parent.categories = ["Informatics"]
    self.parent.dependencies = ["Markups"]
    self.parent.contributors = ["Fryderyk Kögl (TUM, BWH), Harneet Cheema (BWH, UOttawa), Tina Kapur (BWH)"]
    # TODO: update with short description of the module and a link to online module documentation
    self.parent.helpText = """
    Module that gather useful Slicer functionality for setting landmarks in MR and US images. To start choose the
    volumes that you want to use, create an intersection of the US FOV to make sure your landmarks are all in an
    overlapping area and the customise your view. Use the shortcuts listed at the bottom to increase the efficiency of
    the workflow.
    https://github.com/koegl/AmigoStatistics
    """
    self.parent.acknowledgementText = """
    This extension was developed at the Brigham and Women's Hospital by Fryderyk Kögl, Harneet Cheema and Tina Kapur.
    
    This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
    and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
    """


#
# AmigoStatisticsWidget
#
#
class AmigoStatisticsWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
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

    self.single_patient_logic = json_dict_logic.SinglePatientDictLogic()
    self.dict_logic = json_dict_logic.JsonDictLogic()

  def setup(self):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.setup(self)

    # Load widget from .ui file (created by Qt Designer).
    # Additional widgets can be instantiated manually and added to self.layout.
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/AmigoStatistics.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
    # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
    # "setMRMLScene(vtkMRMLScene*)" slot.
    uiWidget.setMRMLScene(slicer.mrmlScene)

    # Create logic class. Logic implements all computations that should be possible to run
    # in batch mode, without a graphical user interface.
    self.logic = AmigoStatisticsLogic()

    # Connections

    # These connections ensure that we update parameter node when scene is closed
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

    # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
    # (in the selected parameter node).

    # Buttons
    # set foreground threshold to 1 for all chosen volumes
    self.ui.hierarchyDumpButton.connect('clicked(bool)', self.onHierarchyDumpButton)
    self.ui.combineHierarchiesButton.connect('clicked(bool)', self.onCombineHierarchiesButton)
    self.ui.printCurrentHierarchyButton.connect('clicked(bool)', self.onPrintCurrentHierarchyButton)
    self.ui.checkCompletenessButton.connect('clicked(bool)', self.onCheckCompletenessButton)
    self.ui.saveToXlsxButton.connect('clicked(bool)', self.onSaveToXlsxButton)

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

  def onHierarchyDumpButton(self):

    try:
      data_summary_path_partial = "/Users/fryderykkogl/Documents/university/master/thesis/code/patient_hierarchy.nosync/patient_summary/patient_data_summary_"
      self.data_summary_paths = []
      self.data_completeness_path = "/Users/fryderykkogl/Documents/university/master/thesis/code/patient_hierarchy.nosync/patient_summary/data_completeness.json"
      igt2_paths_path = "/Users/fryderykkogl/Documents/university/master/thesis/code/patient_hierarchy.nosync/igt2_dropbox_paths.json"

      dropbox_paths = [r"C:\Users\fryde\Dropbox (Partners HealthCare)\Neurosurgery MR-US Registration Data\Case AG2160\Case "
                    r"AG2160 Uncompressed\Case AG2160.mrml",
                    r"C:\Users\fryde\Dropbox (Partners HealthCare)\Neurosurgery MR-US Registration Data\Case AG2146\Case "
                    r"AG2146 Uncompressed\Case AG2146.mrml",
                    r"C:\Users\fryde\Dropbox (Partners HealthCare)\Neurosurgery MR-US Registration Data\Case AG2152\Case "
                    r"AG2152 Uncompressed\Case AG2152.mrml"]

      # read igt2 paths
      igt2_paths_file = open(igt2_paths_path, "r")
      igt2_paths_dict = json.load(igt2_paths_file)
      igt2_paths = igt2_paths_dict["paths"]

      # get paths from UI
      paths_from_ui = self.ui.plainTextEdit.toPlainText()

      if paths_from_ui:  # if they are non empty
        paths = paths_from_ui.split('\n')
      elif igt2_paths:  # if they are non empty
        paths = igt2_paths
      else:
        raise ValueError("No files specified")

      # close any previously opened scene
      slicer.mrmlScene.Clear(0)
      print("\n\n")

      for index, path in enumerate(paths):

        """
        # get id from path
        path_for_id = path.split("/")  # todo do this with os. so its cross platform
        subject_id = path_for_id[-2]
        subject_id = subject_id.split(" ")
        subject_id = subject_id[2]
        
        # for dropbox
        # id = path[-11:-5]
        """

        # if the file exists, continue to the next one
        # if exists(data_summary_path_full):
        #   print("{} was already processed. Skipping to the next one.\n".format(data_summary_path_full))
        #   continue

        try:
          slicer.util.loadScene(path)
        except:  # needs to be so broad because loading causes an error which is irrelevant for the rest of the code
          pass

        try:
          # get id from .mrb
          shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
          slicer.app.ioManager().addDefaultStorageNodes()
          sh_folder_item_id = shNode.GetSceneItemID()
          child_ids = vtk.vtkIdList()
          sh_node = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
          sh_node.GetItemChildren(sh_folder_item_id, child_ids)
          itemIdIndex = 0
          sh_item_id = child_ids.GetId(itemIdIndex)
          case_name = sh_node.GetItemName(sh_item_id)

          case_name_split = case_name.split(' ')
          subject_id = case_name_split[-1]

          data_summary_path_full = data_summary_path_partial + subject_id + ".json"
          self.data_summary_paths.append(data_summary_path_full)

          print('Processing: {}({}/{})'.format(subject_id, index + 1, len(paths)))
          self.single_patient_logic.dump_hierarchy_to_json(subject_id, data_summary_path_full, path)
          print('Finished processing: {}\n\n'.format(subject_id))
        except Exception as e:
          print("Could not process: {}).\nSkipping to the next one.\n({})".format(path, e))
          slicer.mrmlScene.Clear(0)
          continue
        slicer.mrmlScene.Clear(0)

    except:
      slicer.util.errorDisplay("Could not execute onHierarchyDumpButton.\n{}".format(Exception))

  def onCombineHierarchiesButton(self):
    """
    Combine all single hierarchies into one summary
    """

    try:
      # combine single files
      directory_path = "/Users/fryderykkogl/Documents/university/master/thesis/code/patient_hierarchy.nosync" \
                       "/patient_summary"
      summary_file_paths = [join(directory_path, f) for f in listdir(directory_path) if
                            isfile(join(directory_path, f)) and "patient_data_summary" in f]
      self.dict_logic.combine_single_summaries(summary_file_paths, os.path.join(directory_path, "full_summary.json"))

    except:
      slicer.util.errorDisplay("Could not execute onCombineHierarchiesButton.\n{}".format(Exception))

  def onPrintCurrentHierarchyButton(self):
    """
    Prints the current hierarchy
    """

    try:
      print("Current hierarchy:")
      shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
      slicer.app.ioManager().addDefaultStorageNodes()
      all_nodes = self.dict_logic.get_fake_paths_of_all_nodes(shNode.GetSceneItemID())
      for node in all_nodes:
        print(node)

    except:
      slicer.util.errorDisplay("Could not execute onPrintCurrentHierarchyButton.\n{}".format(Exception))

  def onCheckCompletenessButton(self):
    """
    Combine all files check completeness of all files in a given directory
    """

    try:
      # check completeness
      print("\n\n\nChecking completness...")

      directory_path = "/Users/fryderykkogl/Documents/university/master/thesis/code/patient_hierarchy.nosync" \
                       "/patient_summary"

      full_dict_path = os.path.join(directory_path, "full_summary.json")
      full_save_path = os.path.join(directory_path, "full_completeness.json")

      self.dict_logic.dump_full_completenes_dict_to_json(full_dict_path, full_save_path)

      print("\n\n\nCompleteness checked.")

    except:
      slicer.util.errorDisplay("Could not combine and check files.\n{}".format(Exception))
      return

  def onSaveToXlsxButton(self):
    """
    Save the full summary dict to a spreadsheet
    """

    try:
      directory_path = "/Users/fryderykkogl/Documents/university/master/thesis/code/patient_hierarchy.nosync" \
                       "/patient_summary"

      # load full dict
      full_dict_path = os.path.join(directory_path, "full_summary.json")

      full_data = None

      # replace '%' with ' '
      xlsx_exporting_logic.replace_character_in_file(full_dict_path, '%', ' ')

      # load dict
      with open(full_dict_path, 'r') as f:
        full_data = json.load(f)

      if full_data is None:
        raise ValueError("Loaded dict is empty")

      # get max max_lengths
      max_lengths = xlsx_exporting_logic.get_max_lengths_of_data_arrays(full_data)

      # get empty data matrix
      data_matrix = xlsx_exporting_logic.create_empty_data_matrix(len(full_data), sum(max_lengths.values()))

      # fill empty data matrix with values from the summary dict
      data_matrix = xlsx_exporting_logic.fill_empty_matrix_with_summary_dict(full_data, data_matrix, max_lengths)

      # format the data_matrix to a spreadsheet
      writer = xlsx_exporting_logic.format_data_matrix_to_excel(data_matrix, max_lengths,
                                                                os.path.join(directory_path, "full_summary.xlsx"))

      # save the spreadsheet
      writer.save()

    except:
      slicer.util.errorDisplay("Could not execute onSaveToXlsxButton.\n{}".format(Exception))


#
# AmigoStatisticsLogic
#

class AmigoStatisticsLogic(ScriptedLoadableModuleLogic):
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
# AmigoStatisticsTest
#
#
class AmigoStatisticsTest(ScriptedLoadableModuleTest):
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
    self.test_AmigoStatistics1()

  def test_AmigoStatistics1(self):
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

    logic = AmigoStatisticsLogic()

    pass

    self.delayDisplay('Test passed')

