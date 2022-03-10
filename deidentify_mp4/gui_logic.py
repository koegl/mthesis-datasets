from deidentify_mp4.export_logic import ExportHandling

import dearpygui.dearpygui as dpg


class GUIWindow:
    def __init__(self,):
        dpg.create_context()
        dpg.create_viewport(title='', width=600, height=300)

        self.load_paths = ""

        self.export_handler = ExportHandling()

    def crop_callback(self):

        # convert string into a list
        path_list = []
        for path in self.load_paths.splitlines():
            path_list.append(path)

        self.export_handler.run_export_main(path_list)

    def _log(self, sender, app_data, user_data):
        self.load_paths = app_data

    def main(self):
        with dpg.window(label="Crop files"):
            dpg.add_button(label="Crop", callback=self.crop_callback)

            dpg.add_text("\nAdd paths to the files that you want to convert:\n"
                         "NOTES:\n"
                         "\t- each path has to be in a new line\n"
                         "\t- each cropped file is saved in the same directory as the original file\n"
                         "\t- the error log is saved in the directory where the first file is saved\n"
                         "\t- the amount of pixels cropped is fixed - it is dialed in for clips such as lung US")
            dpg.add_input_text(label="", callback=self._log, multiline=True)

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()
