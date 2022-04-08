import matplotlib.pyplot as plt
import numpy as np

for i in range(10):
    x = np.random.rand(100, 100)
    plt.ion()
    plt.figure()
    plt.imshow(x)
    plt.show()
    _ = input("Press [enter] to continue.")
    plt.close()
