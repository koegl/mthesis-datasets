# script_path = "C:\\Users\\fryde\\Documents\\university\\master\\thesis\\code\\mthesis-datasets\\mrb_hierarchy_extractor.py"
# eval(open('/tmp/code.py').read())


def export_nodes(sh_folder_item_id, output_folder, f):
    # Get items in the folder
    child_ids = vtk.vtkIdList()
    sh_node = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    sh_node.GetItemChildren(sh_folder_item_id, child_ids)
    if child_ids.GetNumberOfIds() == 0:
        return
    # Create output folder
    import os
    os.makedirs(output_folder, exist_ok=True)
    # Write each child item to file
    for itemIdIndex in range(child_ids.GetNumberOfIds()):
        sh_item_id = child_ids.GetId(itemIdIndex)
        # Write node to file (if storable)
        data_node = sh_node.GetItemDataNode(sh_item_id)
        if data_node and data_node.IsA("vtkMRMLStorableNode") and data_node.GetStorageNode():
            storage_node = data_node.GetStorageNode()
            filename = os.path.basename(storage_node.GetFileName())
            filepath = output_folder + "________" + filename
            f.write(filepath+"\n")
        # Write all children of this child item
        grand_child_ids = vtk.vtkIdList()
        sh_node.GetItemChildren(sh_item_id, grand_child_ids)
        if grand_child_ids.GetNumberOfIds() > 0:
            export_nodes(sh_item_id, output_folder + "/" + sh_node.GetItemName(sh_item_id), f)

scene_path = "C:\\Users\\fryde\\Documents\\university\\master\\thesis\\datasets\\slicer_scenes\\hierarchy_test\\2021-12-20-Scene.mrml"
hierarchy_file_path = "C:\\Users\\fryde\\Documents\\university\\master\\thesis\\code\\mthesis-datasets\\hierarchy.txt"
slicer.util.loadScene(scene_path)

f = open(hierarchy_file_path, "a")
f.write("starting with writing\n\n\n")
shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
outputFolder = "c:/tmp/test20211123"
slicer.app.ioManager().addDefaultStorageNodes()
export_nodes(shNode.GetSceneItemID(), outputFolder, f)
f.write("\n\n\ndone with writing")
f.close()

sys.exit(0)
