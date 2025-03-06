# SPDX-FileCopyrightText: 2022 Jeff Epler for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""Compute an inverse polar transform

This can warp an image from linear to polar.

It is not quite the inverse of the skimage polar mapping, but it performs the
task needed for fluxvis
"""

import numpy as np

from skimage import data
from skimage.transform import warp


def _inverse_polar_mapping(output_coords, k_angle, k_radius, center):
    """Compute an inverse polar mapping"""
    yy = output_coords[:, 0] - center[0]
    xx = output_coords[:, 1] - center[1]
    cc = (np.pi + np.arctan2(-yy, xx)) * k_angle
    rr = np.hypot(yy, xx) * k_radius
    return np.column_stack((cc, rr))


def warp_inverse_polar(
    image, center=None, *, radius=None, output_shape=None, multichannel=False, **kwargs
):
    """Warp an image from linear to polar"""
    if image.ndim != 2 and not multichannel:
        raise ValueError(
            "Input array must be 2 dimensions "
            "when `multichannel=False`,"
            " got {}".format(image.ndim)
        )

    if image.ndim != 3 and multichannel:
        raise ValueError(
            "Input array must be 3 dimensions "
            "when `multichannel=True`,"
            " got {}".format(image.ndim)
        )

    if output_shape is None:
        output_shape = np.array((960, 960))
    else:
        output_shape = np.array(output_shape[:2])

    input_shape = np.array(image.shape)[:2]
    if center is None:
        center = (output_shape[:2] / 2) - 0.5

    if radius is None:
        width, height = output_shape[:2] / 2
        radius = np.hypot(width, height) / np.sqrt(2)

    height = input_shape[0]
    width = input_shape[1]

    k_radius = height / radius
    k_angle = (width - 1) / (2 * np.pi)

    warp_args = {"k_angle": k_angle, "k_radius": k_radius, "center": center}
    warped = warp(
        image,
        _inverse_polar_mapping,
        map_args=warp_args,
        output_shape=output_shape,
        **kwargs,
    )

    return warped


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    checkerboard = data.checkerboard()

    fig, axes = plt.subplots(1, 2, figsize=(8, 8))
    ax = axes.ravel()
    ax[0].set_title("Original")
    ax[0].imshow(checkerboard)
    ax[1].set_title("Original, Inverse-Polar-Transformed")
    ax[1].imshow(warp_inverse_polar(checkerboard))
    plt.show()
