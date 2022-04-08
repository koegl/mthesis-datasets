import matplotlib.pyplot as plt
import os

from utils_inspect import load_mp4, extract_file_paths_with_extension


class FileInspector:
    def __init__(self, directory, extension="mp4"):
        self.directory = directory
        self.extension = extension

        self.save_path = ""

        self.mp4_paths = []
        self.accepted = []
        self.rejected = []

        self.extract_mp4s()

    def extract_mp4s(self):
        if isinstance(self.directory, str):
            self.mp4_paths = extract_file_paths_with_extension(self.directory, self.extension, exclude="horos")
            self.save_path = self.directory + "/accepted.txt"
        elif isinstance(self.directory, list):
            for dir in self.directory:
                self.mp4_paths += extract_file_paths_with_extension(dir, self.extension, exclude="horos")

            # move up one directory from path
            parent_path = self.directory[0].split("/")
            parent_path = "/".join(parent_path[:-1])

            self.save_path = parent_path + "/rejected.txt"

    def write_list_to_file(self, file_path, list_to_write):

        if os.path.exists(file_path):
            with open(file_path, "a") as f:
                for item in list_to_write:
                    f.write("%s\n" % item)
        else:
            with open(file_path, "w+") as f:
                for item in list_to_write:
                    f.write("%s\n" % item)

    def inspect(self):
        for idx, path in enumerate(self.mp4_paths):

            # load first frame of a video
            frame = load_mp4(path)[0]

            # plot the frame
            plt.ion()
            plt.figure()
            plt.imshow(frame)
            plt.title(f"Frame: {idx+1}/{len(self.mp4_paths)}")
            plt.show()

            os.system("clear")
            b = f"Accept (Enter);\t\treject (q);\tstop (s): "
            user_input = input(b)
            os.system("clear")

            plt.close()

            if user_input == "":
                self.accepted.append(path)
            elif user_input == "q":
                self.rejected.append(path)
            elif user_input == "s":
                self.rejected.append("\n\n\n\nLast path which has to be checked again\n" + path + "\n\n\n\n")
                break

        self.write_list_to_file(self.save_path, self.rejected)

