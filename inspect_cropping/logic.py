import matplotlib.pyplot as plt
import os

from utils_inspect import load_mp4, extract_file_paths_with_extension


class FileInspector:
    def __init__(self, directory, extension="mp4", step_size=8, frame_rate=1/30, subsample=None):
        self.directory = directory
        self.extension = extension

        self.save_path = ""

        self.mp4_paths = []
        self.accepted = []
        self.rejected = []

        self.extract_mp4s()

        # display speed parameters
        self.step_size = step_size
        self.frame_rate = frame_rate
        self.subsample = subsample

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
        idx = 0

        while idx < len(self.mp4_paths):
            path = self.mp4_paths[idx]

            # load first frame of a video
            video = load_mp4(path, subsample=self.subsample)

            plt.axis([0, 10, 0, 1])

            plt.ion()
            plt.figure()
            plt.title(f"Frame: {idx + 1}/{len(self.mp4_paths)}")

            image = plt.imshow(video[0])

            for i in range(1, int(video.shape[0] / self.step_size)):
                # plot the frame
                plt.pause(self.frame_rate)
                image.set_data(video[self.step_size * i])

            plt.show()

            os.system("clear")
            b = f"Accept (Enter);\t\treject (q);\trepeat (r);\tstop (s): "
            user_input = input(b)
            os.system("clear")

            plt.close()

            if user_input == "":
                self.accepted.append(path)
            elif user_input.lower() == "q":
                self.rejected.append(path)
            elif user_input.lower() == "r":
                continue
            elif user_input.lower() == "s":
                self.rejected.append("\n\n\n\nLast path which has to be checked again\n" + path + "\n\n\n\n")
                break
            else:
                continue

            idx += 1

        self.write_list_to_file(self.save_path, self.rejected)

