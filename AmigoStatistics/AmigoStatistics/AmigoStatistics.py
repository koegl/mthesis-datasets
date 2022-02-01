import unittest
import numpy as np
import logging
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import SegmentEditorEffects
import functools
import os
from os.path import exists
import json
import random
from os import listdir
from os.path import isfile, join

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
    self.ui.printCurrentHierarchyButton.connect('clicked(bool)', self.onPrintCurrentHierarchyButton)
    self.ui.checkCompletenessButton.connect('clicked(bool)', self.onCheckCompletenessButton)

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

  @staticmethod
  def create_empty_dict_entry(dictionary, mrm, path):
    """
    Add an empty dict entry
    """

    dictionary[mrm] = {
      "path": [path],
      "pre-op imaging": [],
      "intra-op imaging": {
        "ultrasounds": [],
        "rest": []
      },
      "continuous tracking data": {
        "pre-imri tracking": [],
        "post-imri tracking": []
      },
      "segmentations": {
        "pre-op fmri segmentations": [],
        "pre-op brainlab manual dti tractography segmentations": [],
        "rest": []
      }
    }

    return dictionary

  def populate_dict_with_hierarchy(self, sh_folder_item_id, patient_id, storage_dict, scene_path, hierarchy_ori=None):
    """
    Populate a dict entry with the hierarchy of an opened scene
    """

    hierarchy = hierarchy_ori

    if not hierarchy_ori:
      hierarchy_ori = ""

    if not hierarchy:
      hierarchy = ""
    else:
      hierarchy = hierarchy.split('/')
      del hierarchy[0]

      if any(x in hierarchy[0].lower() for x in ["patient", patient_id]):
        del hierarchy[0]  # remove first element because it's the patient case

    child_ids = vtk.vtkIdList()
    sh_node = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    sh_node.GetItemChildren(sh_folder_item_id, child_ids)
    if child_ids.GetNumberOfIds() == 0:
      return

    # Write each child item to file
    for itemIdIndex in range(child_ids.GetNumberOfIds()):
      sh_item_id = child_ids.GetId(itemIdIndex)
      # Write node to file (if storable)
      data_node = sh_node.GetItemDataNode(sh_item_id)
      if data_node and data_node.IsA("vtkMRMLStorableNode") and data_node.GetStorageNode():
        storage_node = data_node.GetStorageNode()
        filename = os.path.basename(storage_node.GetFileName())

        if patient_id not in storage_dict:
          storage_dict = self.create_empty_dict_entry(storage_dict, patient_id, scene_path)

        if not hierarchy:  # we are at the end
          return storage_dict

        if all(x in hierarchy[0].lower() for x in ["pre", "op", "imaging"]):
          storage_dict[patient_id]["pre-op imaging"].append(filename)

        elif all(x in hierarchy[0].lower() for x in ["intra", "op", "imaging"]):
          if len(hierarchy) == 1:
            storage_dict[patient_id]["intra-op imaging"]["rest"].append(filename)
          else:
            storage_dict[patient_id]["intra-op imaging"]["ultrasounds"].append(filename)

        elif all(x in hierarchy[0].lower() for x in ["contin", "tracking"]):
          if len(hierarchy) == 1:
            if "post" in filename.lower():
              storage_dict[patient_id]["continuous tracking data"]["post-imri tracking"].append(filename)
            else:
              storage_dict[patient_id]["continuous tracking data"]["pre-imri tracking"].append(filename)

          elif all(x in hierarchy[1].lower() for x in ["pre", "imri", "tracking"]):
            storage_dict[patient_id]["continuous tracking data"]["pre-imri tracking"].append(filename)
          elif all(x in hierarchy[1].lower() for x in ["post", "imri", "tracking"]):
            storage_dict[patient_id]["continuous tracking data"]["post-imri tracking"].append(filename)

        elif "segmentations" in hierarchy[0].lower():
          if len(hierarchy) == 1:
            storage_dict[patient_id]["segmentations"]["rest"].append(filename)
          elif all(x in hierarchy[1].lower() for x in ["pre-op", "fmri"]):
            storage_dict[patient_id]["segmentations"]["pre-op fmri segmentations"].append(filename)
          elif all(x in hierarchy[1].lower() for x in ["brainlab", "dti"]):
            storage_dict[patient_id]["segmentations"]["pre-op brainlab manual dti tractography segmentations"].append(filename)

      # Write all children of this child item
      grand_child_ids = vtk.vtkIdList()
      sh_node.GetItemChildren(sh_item_id, grand_child_ids)
      if grand_child_ids.GetNumberOfIds() > 0:
        self.populate_dict_with_hierarchy(sh_item_id, patient_id, storage_dict, scene_path,
                                     hierarchy_ori + "/" + sh_node.GetItemName(sh_item_id))

    return storage_dict

  def dump_hierarchy_to_json(self, patient_id, data_json_path, scene_path):
    """
    Dumps entire hierarchy to a json
    """
    print('Processing: {}\n'.format(patient_id))

    if exists(data_json_path):
      # check if file is empty
      if os.stat(data_json_path).st_size == 0:
        patients_dict = {}
        os.remove(data_json_path)
      else:  # if not empty, we can load it (we assume it is correct)
        load_file = open(data_json_path, "r+")
        patients_dict = json.load(load_file)
        load_file.truncate(0)  # clear file so we can store the updated dict
        load_file.close()
        os.remove(data_json_path)
    else:
      patients_dict = {}

    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    slicer.app.ioManager().addDefaultStorageNodes()

    if str(patient_id) not in patients_dict:  # it was already parsed at some point
      patients_dict = self.populate_dict_with_hierarchy(shNode.GetSceneItemID(), patient_id, patients_dict, scene_path)

      f = open(data_json_path, "a")
      json.dump(patients_dict, f)
      f.close()

    print('Finished rocessing: {}\n'.format(patient_id))

  def check_dictionary_for_completeness(self, data_dict):
    """
    Check if each array in the dict is populated, if not write some kind of error log
    """
    data_missing = {}

    for key, item in data_dict.items():
      data_missing[key] = [item["path"]]

      if len(item["pre-op imaging"]) == 0:
        data_missing[key].append("pre-op imaging")

      if len(item["intra-op imaging"]["ultrasounds"]) == 0:
        data_missing[key].append("intra-op imaging - ultrasounds")
      if len(item["intra-op imaging"]["rest"]) == 0:
        data_missing[key].append("intra-op imaging - rest")

      if len(item["continuous tracking data"]["pre-imri tracking"]) == 0:
        data_missing[key].append("continuous tracking data - pre-imri tracking")
      if len(item["continuous tracking data"]["post-imri tracking"]) == 0:
        data_missing[key].append("continuous tracking data - post-imri tracking")

      if len(item["segmentations"]["pre-op fmri segmentations"]) == 0:
        data_missing[key].append("segmentations - pre-op fmri segmentations")
      if len(item["segmentations"]["pre-op brainlab manual dti tractography segmentations"]) == 0:
        data_missing[key].append("segmentations - pre-op brainlab manual dti tractography segmentations")
      if len(item["segmentations"]["rest"]) == 0:
        data_missing[key].append("segmentations - rest")

      if len(data_missing[key]) == 1:  # if nothing missing was found, remove the entry (1 means we only added the path)
        del data_missing[key]

    return data_missing

  def dump_full_completenes_dict_to_json(self, summary_paths, save_path):
    """
    Gather all summary files and combine into one completness dict
    """

    data_missing = []

    for data_summary_path in summary_paths:
      # check if dict contains something
      if not exists(data_summary_path):
        print("{} to check for completeness could not be found".format(data_summary_path))
        continue
      if os.stat(data_summary_path).st_size == 0:
        print("No data found in the .json to check for completeness")
        continue

      # load dict with all data
      load_file = open(data_summary_path, "r")
      patients_check_dict = json.load(load_file)
      load_file.close()

      # create dict specifying what is missing
      if not patients_check_dict:  # if dict is empty
        data_missing.append({data_summary_path: "NO DATA COULD BE EXTRACTED"})
      else:
        data_missing.append(self.check_dictionary_for_completeness(patients_check_dict))

    # delete the json completeness file if a previous version exists
    if exists(save_path):
      os.remove(save_path)

    # save completeness dict
    completeness_file = open(save_path, "w+")
    completeness_file.truncate(0)
    json.dump(data_missing, completeness_file)
    completeness_file.close()

    for missing in data_missing:
      for key, item in missing.items():
        if len(item) > 0:
          print("\nCase {} misses the following data:\n{}\n".format(key, item))

  def onHierarchyDumpButton(self):

    data_summary_path_partial = "/Users/fryderykkogl/Data/patient_hierarchy/patient_summary/patient_data_summary_"
    self.data_summary_paths = []
    self.data_completeness_path = "/Users/fryderykkogl/Data/patient_hierarchy/patient_summary/data_completeness.json"
    igt2_paths_path = "/Users/fryderykkogl/Data/patient_hierarchy/igt2_paths.json"

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

    # close any previously opened scene
    slicer.mrmlScene.Clear(0)

    for path in igt2_paths:
      # get id
      path_for_id = path.split("/")  # todo do this with os. so its cross platform
      subject_id = path_for_id[-2]
      subject_id = subject_id.split(" ")
      subject_id = subject_id[2]

      # for dropbox
      # id = path[-11:-5]

      data_summary_path_full = data_summary_path_partial + subject_id + ".json"
      self.data_summary_paths.append(data_summary_path_full)

      # if the file exists, continue to the next one
      if exists(data_summary_path_full):
        continue

      slicer.util.loadScene(path)
      try:
        self.dump_hierarchy_to_json(patient_id=subject_id, data_json_path=data_summary_path_full, scene_path=path)
      except Exception as e:
        print("Could not process patient {} (path: {}). Skipping to the next one.\n({})".format(subject_id, path, e))
        slicer.mrmlScene.Clear(0)
        continue
      slicer.mrmlScene.Clear(0)

    # check completeness
    print("\n\n\nChecking completness...")

    self.dump_full_completenes_dict_to_json(self.data_summary_paths, self.data_completeness_path)

    print("\n\n\nCompleteness checked.")

  def onPrintCurrentHierarchyButton(self):
    """
    Prints the current hierarchy
    """
    print("Current hierarchy:")
    def exportNodes(shFolderItemId, outputFolder=""):
      # Get items in the folder
      childIds = vtk.vtkIdList()
      shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
      shNode.GetItemChildren(shFolderItemId, childIds)
      if childIds.GetNumberOfIds() == 0:
        return

      # Write each child item to file
      for itemIdIndex in range(childIds.GetNumberOfIds()):
        shItemId = childIds.GetId(itemIdIndex)

        # Write node to file (if storable)
        dataNode = shNode.GetItemDataNode(shItemId)
        if dataNode and dataNode.IsA("vtkMRMLStorableNode") and dataNode.GetStorageNode():
          storageNode = dataNode.GetStorageNode()
          filename = os.path.basename(storageNode.GetFileName())
          filepath = outputFolder + "/" + filename
          print(filepath)

        # Write all children of this child item
        grandChildIds = vtk.vtkIdList()
        shNode.GetItemChildren(shItemId, grandChildIds)
        if grandChildIds.GetNumberOfIds() > 0:
          exportNodes(shItemId, outputFolder + "/" + shNode.GetItemName(shItemId))

    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    slicer.app.ioManager().addDefaultStorageNodes()
    exportNodes(shNode.GetSceneItemID())

  def onCheckCompletenessButton(self):
    """
    Combine all files check completeness of all files in a given directory
    """

    # combine all files
    directory_path = r"C:\Users\fryde\Documents\university\master\thesis\code\patient_summary"
    summary_files = [join(directory_path, f) for f in listdir(directory_path) if isfile(join(directory_path, f)) and "summary" in f]
    summary_dicts = []

    for file in summary_files:
      f = open(file, "r")
      summary_dicts.append(json.load(f))

    self.dump_full_completenes_dict_to_json(self.data_summary_paths, self.data_completeness_path)

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

