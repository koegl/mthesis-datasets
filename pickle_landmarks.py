# Script to export landmarks for S without opening slicer etc.
# To run this script, paste the following into the terminal: (MacOS)
# /Applications/Slicer.app/Contents/MacOS/Slicer --no-splash --no-main-window --python-script "/Users/fryderykkogl/Documents/university/master/thesis/code/SlicerMRUSLandmarking/MRUSLandmarking/Resources/Logic/test.py"
# if you don't add command line arguments at the end, the defaults will be used

import slicer

import pickle
import sys
import argparse


def export_landmarks_to_numpy(markups_list_name, output_path):
    """
    Export Slicer landmarks to numpy landmarks (S). Format of the landmarks for two corresponding volumes:
    n - amount of landmarks. we create a tuple of two volumes (for 5 volumes a tuple of 5)

    landmarks = (ndarray: (n,3), ndarray(n,3))
    """
    try:
        point_list_node = slicer.util.getNode(markups_list_name)
    except Exception as e:
        slicer.util.errorDisplay("Wrong name of markups list. Try again.\n{}".format(e))
        return

    # Get markup positions
    data = ([], [], [], [], [])
    index = 0

    for i in range(int(point_list_node.GetNumberOfControlPoints() / 5)):
        for j in range(5):
            coords = [0, 0, 0]

            point_list_node.GetNthControlPointPosition(index, coords)

            if "pre-op" in point_list_node.GetNthControlPointLabel(index).lower():
                volume_idx = 0
            elif "us1" in point_list_node.GetNthControlPointLabel(index).lower():
                volume_idx = 1
            elif "us2" in point_list_node.GetNthControlPointLabel(index).lower():
                volume_idx = 2
            elif "us3" in point_list_node.GetNthControlPointLabel(index).lower():
                volume_idx = 3
            elif "intra-op" in point_list_node.GetNthControlPointLabel(index).lower():
                volume_idx = 4
            else:
                slicer.util.errorDisplay("Wrong fiducial names. Exiting without exporting.")
                return

            data[volume_idx].append(coords)

            index += 1

    with open(output_path, 'ab') as pickle_file:
      pickle.dump(data, pickle_file)


def main(params):
    # debug
    try:
        slicer.util.loadScene(params.mrb_path)

        export_landmarks_to_numpy(params.markups_list_name, params.export_path)
        sys.exit(0)

    except Exception as e:
        print(f"could not export.\n{e}")
        sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-mrb", "--mrb_path", type=str, help="Path to the the mrb to load",
                        default='/Users/fryderykkogl/Dropbox (Partners HealthCare)/Neurosurgery MR-US Registration Data'
                                '/Case AG2152/Harneet/AG2152-H editedL10.mrb')
    parser.add_argument("-mln", "--markups_list_name", type=str, help="Name of the markups list",
                        default="AG2152")
    parser.add_argument("-ep", "--export_path", type=str, help="Path to the pickle export",
                        default="/Users/fryderykkogl/Desktop/AG2152")

    arguments = parser.parse_args()

    main(arguments)
