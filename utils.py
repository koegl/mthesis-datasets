import matplotlib.pyplot as plt
import numpy as np


def volumetric_plot(image, volume_type="label", threshold=0.1):

    # convert to numpy array
    image = image.get_fdata()
    image = np.asarray(image)

    # make binary
    image[image < threshold] = 0
    image[image >= threshold] = 1

    # volumetric visualisation
    voxels = image.astype(bool)
    colors = np.empty(voxels.shape, dtype=object)
    colors[voxels] = 'red'

    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.voxels(voxels, facecolors=colors, edgecolor='none')

    ax.set_title(volume_type)

    plt.show()
