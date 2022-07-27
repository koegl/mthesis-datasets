import argparse
import numpy as np
import matplotlib.pyplot as plt
import nibabel as nib
import nrrd
import os


def main(params):
    image1 = nib.load(params.first_image)
    image2 = nib.load(params.second_image)

    t1 = image1.affine
    t2 = image2.affine

    registration = np.matmul(t2, np.linalg.inv(t1))
    registration = np.linalg.inv(registration)

    f00 = registration[0, 0]
    f01 = registration[0, 1]
    f02 = registration[0, 2]
    f03 = registration[0, 3]
    f10 = registration[1, 0]
    f11 = registration[1, 1]
    f12 = registration[1, 2]
    f13 = registration[1, 3]
    f20 = registration[2, 0]
    f21 = registration[2, 1]
    f22 = registration[2, 2]
    f23 = registration[2, 3]

    line1 = "#Insight Transform File V1.0"
    line2 = "#Transform 0"
    line3 = f"Transform: AffineTransform_double_3_3"
    line4 = f"Parameters: {f00} {f01} {-f02} {f10} {f11} {-f12} {-f20} {-f21} {f22} {-f03} {-f13} {f23}"
    line5 = "FixedParameters: 0 0 0"

    save_path = os.path.join('/'.join(params.first_image.split('/')[:-1]), 'registration.tfm')

    with open(save_path, 'w') as f:
        f.write(line1 + '\n')
        f.write(line2 + '\n')
        f.write(line3 + '\n')
        f.write(line4 + '\n')
        f.write(line5 + '\n')

    print("DONE")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-fi", "--first_image",
                        default="/Users/fryderykkogl/Dropbox (Partners HealthCare)/TCIA/3. TCIA cases - images and segmentations/mrbs/"
                                "20210921_craini_bi IN PROGRESS/Data/US1.nii",
                        help="Path to the trained .pt model file")
    parser.add_argument("-si", "--second_image",
                        default="/Users/fryderykkogl/Dropbox (Partners HealthCare)/TCIA/3. TCIA cases - images and segmentations/mrbs/"
                                "20210921_craini_bi IN PROGRESS/Data/US1_reg.nii",
                        help="Path to the trained .pt model file")

    args = parser.parse_args()

    main(args)
