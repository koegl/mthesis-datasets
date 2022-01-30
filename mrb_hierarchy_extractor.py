# script_path = "C:\\Users\\fryde\\Documents\\university\\master\\thesis\\code\\mthesis-datasets\\mrb_hierarchy_extractor.py"
# eval(open('C:\\Users\\fryde\\Documents\\university\\master\\thesis\\code\\mthesis-datasets\\simple.py').read())
# command to run the script from the terminal
# C:\Users\fryde\AppData\Local\NA-MIC\"Slicer 4.13.0-2022-01-28">Slicer.exe --python-script C:\Users\fryde\Documents\university\master\thesis\code\mthesis-datasets\mrb_hierarchy_extractor.py
# you need to be in the slicer folder
import os


def export_nodes(sh_folder_item_id, f, hierarchy=None):
    if not hierarchy:
        hierarchy = []

    child_ids = vtk.vtkIdList()


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
            filepath = hierarchy + "________" + filename
            f.write(filepath+"\n")
        # Write all children of this child item
        grand_child_ids = vtk.vtkIdList()
        sh_node.GetItemChildren(sh_item_id, grand_child_ids)
        if grand_child_ids.GetNumberOfIds() > 0:
            export_nodes(sh_item_id, f, hierarchy + "/" + sh_node.GetItemName(sh_item_id))


scene_path = "C:\\Users\\fryde\\Documents\\university\\master\\thesis\\datasets\\slicer_scenes\\hierarchy_test\\2021-12-20-Scene.mrml"
scene_path_amigo = "C:\\Users\\fryde\Dropbox (Partners HealthCare)\\Neurosurgery MR-US Registration Data\\Case AG2146\\Case AG2146 Uncompressed\\Case AG2146.mrml"
hierarchy_file_path = "C:\\Users\\fryde\\Documents\\university\\master\\thesis\\code\\mthesis-datasets\\hierarchy.txt"

f = open(hierarchy_file_path, "a")

f.write("before opening\n\n\n")

# slicer.util.loadScene(scene_path_amigo)


f.write("starting with writing\n\n\n")
shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
outputFolder = "c:/tmp/test20211123"
slicer.app.ioManager().addDefaultStorageNodes()
export_nodes(shNode.GetSceneItemID(), f)
f.write("\n\n\ndone with writing")
f.close()

sys.exit(0)
