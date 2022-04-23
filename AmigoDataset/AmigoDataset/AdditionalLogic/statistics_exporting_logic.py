from AdditionalLogic.structure_logic import StructureLogic
from AdditionalLogic.tree import Tree


class StatisticsExportingLogic:
    """
    Class to encapsulate logic for exporting mrb volume statistics.
    """

    def __init__(self):
        self.folder_structure = None

    def export_current_scene(self, export_path=None):

        # load structure tree
        self.folder_structure = StructureLogic.bfs_generate_folder_structure_as_tree()

        if export_path is None:  # then just print the stats
            self.folder_structure.print_tree()
            pass

    def export_multiple_scenes(self, mrb_pats, export_path=None):

        if export_path is None:  # then just print the stats
            print("printing stats")
            pass

