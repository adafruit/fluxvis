import numpy as np

from skimage import data
from skimage.transform import warp_polar, warp
from skimage.transform._warps import _linear_polar_mapping as polar_mapping

def inverse_polar_mapping(output_coords, k_angle, k_radius, center):
    xx = output_coords[:, 0] - center[0]
    yy = output_coords[:, 1] - center[1]
    cc = (np.pi + np.arctan2(yy, xx)) * k_angle
    rr = np.hypot(yy, xx) * k_radius
    return np.column_stack((cc, rr))

def warp_inverse_polar(image, center=None, *, radius=None, output_shape=None, multichannel=False, **kwargs):
    if image.ndim != 2 and not multichannel:
        raise ValueError("Input array must be 2 dimensions "
                         "when `multichannel=False`,"
                         " got {}".format(image.ndim))

    if image.ndim != 3 and multichannel:
        raise ValueError("Input array must be 3 dimensions "
                         "when `multichannel=True`,"
                         " got {}".format(image.ndim))

    if output_shape is None:
        output_shape = np.array((960, 960))
    else:
        output_shape = np.array(output_shape[:2])

    input_shape = np.array(image.shape)[:2]
    if center is None:
        center = (output_shape[:2] / 2) - 0.5

    if radius is None:
        w, h = output_shape[:2] / 2
        radius = np.hypot(w, h) / np.sqrt(2)

    height = input_shape[0]
    width = input_shape[1]

    k_radius = height / radius
    k_angle = width / (2 * np.pi)

    warp_args = {'k_angle': k_angle, 'k_radius': k_radius, 'center': center}
    warped = warp(image, inverse_polar_mapping, map_args=warp_args, output_shape=output_shape, **kwargs)

    return warped

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    image = data.checkerboard()

    fig, axes = plt.subplots(1, 2, figsize=(8, 8))
    ax = axes.ravel()
    ax[0].set_title("Original")
    ax[0].imshow(image)
    ax[1].set_title("Original, Inverse-Polar-Transformed")
    ax[1].imshow(warp_inverse_polar(image))
    plt.show()
