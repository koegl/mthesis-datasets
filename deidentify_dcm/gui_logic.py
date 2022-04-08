from deidentify_dcm.export_logic import ExportHandling
from deidentify_dcm.utils_deidentify import extract_dicom_and_movie_file_paths
import dearpygui.dearpygui as dpg


class GUIWindow:
    def __init__(self,):
        dpg.create_context()
        dpg.create_viewport(title='', width=600, height=300)

        self.load_paths = ""
        self.load_folder = ""

        self.export_handler = ExportHandling()

        self.top = 0.0
        self.bottom = 0.0
        self.left = 0.0
        self.right = 0.0

    def error_message_crop(self, error_message):

        # guarantee these commands happen in the same frame
        with dpg.mutex():
            viewport_width = dpg.get_viewport_client_width()
            viewport_height = dpg.get_viewport_client_height()

            with dpg.window(label=error_message, modal=True, no_close=True) as modal_id:
                dpg.add_button(label="Ok", width=75, user_data=(modal_id, True), callback=self.close_error_message_crop)

        # guarantee these commands happen in another frame
        dpg.split_frame()
        width = dpg.get_item_width(modal_id)
        height = dpg.get_item_height(modal_id)
        dpg.set_item_pos(modal_id, [viewport_width // 2 - width // 2, viewport_height // 2 - height // 2])

    def close_error_message_crop(self, sender, unused, user_data):
        dpg.delete_item(user_data[0])

    def crop_callback(self):

        # error when both fields with paths are empty
        if self.load_paths == "" and self.load_folder == "":
            self.error_message_crop(error_message="Empty paths")
        elif self.load_paths != "" and self.load_folder != "":
            self.error_message_crop(error_message="Specify only file paths or folder path")

        # get all crop values
        crop_values = [self.top, self.bottom, self.left, self.right]

        for i, value in enumerate(crop_values):
            try:
                crop_values[i] = float(value)
            except:
                self.error_message_crop(error_message="Wrong crop values (not numbers)")
                return

        # get paths as a list
        path_list = []
        if self.load_folder == "":  # if the user passed paths
            for path in self.load_paths.splitlines():
                path_list.append(path)

        elif self.load_paths == "":  # if the user passed folder
            path_list = extract_dicom_and_movie_file_paths(self.load_folder)

        path_list.sort()

        self.export_handler.run_export_loop(path_list, crop_values)

    def update_paths(self, sender, app_data, user_data):
        self.load_paths = app_data

    def update_folder(self, sender, app_data, user_data):
        self.load_folder = app_data

    def update_top(self, sender, app_data, user_data):
        self.top = app_data

    def update_bottom(self, sender, app_data, user_data):
        self.bottom = app_data

    def update_left(self, sender, app_data, user_data):
        self.left = app_data

    def update_right(self, sender, app_data, user_data):
        self.right = app_data

    def main(self):
        with dpg.window(label="Crop DICOM/mp4/mpv/avi files"):

            dpg.set_viewport_width(650)
            dpg.set_viewport_height(430)

            dpg.add_button(label="Crop", callback=self.crop_callback)

            dpg.add_text("Enter the amount of crop for top, bottom, left, right (e.g. 0.3 corresponds to 30%)\n"
                         "(\'0.09166\' works well for top)")
            with dpg.group(horizontal=True):
                dpg.add_input_text(label="Top\t", callback=self.update_top, width=60,  default_value="0.0")
                dpg.add_input_text(label="Bottom\t", callback=self.update_bottom, width=60, default_value="0.0")
                dpg.add_input_text(label="Left\t", callback=self.update_left, width=60, default_value="0.0")
                dpg.add_input_text(label="Right\t", callback=self.update_right, width=60, default_value="0.0")

            dpg.add_text("\n\n\nAdd paths to the separate files (first entry box) or a path to a folder (second entry "
                         "box)")
            dpg.add_text("\nAdd paths to the DICOM/mp4/mpv/avi files that you want to convert:\n"
                         "NOTES:\n"
                         "\t- each path has to be in a new line\n"
                         "\t- each cropped files are saved in the directory above in a sub-directory 'deientified'\n"
                         "\t- the error log is saved in the desktop as 'deidentify.log'\n")
            dpg.add_input_text(label="", callback=self.update_paths, multiline=True)
            dpg.add_text("\nAdd path to the main folder (all dicoms, mp4, mpv andavi will be extracted automatically")
            dpg.add_input_text(label="", callback=self.update_folder, multiline=False)

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()
