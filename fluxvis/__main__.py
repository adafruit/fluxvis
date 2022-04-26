# SPDX-FileCopyrightText: 2022 Jeff Epler for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""Flux visualizer"""

import numpy as np
import click
from skimage.io import imsave
from . import open_flux, render_flux, circularize


@click.command()
@click.option(
    "--slices",
    default=4000,
    help="The angular resolution of the flux in 1/revolution (default: 4000)",
)
@click.option("--stacks", default=6, help="The pixel thickness of a track (default: 6)")
@click.option(
    "--diameter",
    default=216.0,
    help="The diameter of the outermost track, in track-widths."
    'A 5.25" HD disk is approximately 216, 3.5" HD disk is approximately 420. '
    "Halve for DD. (default: 216)",
)
@click.option("--tracks", default=80, help="The total count of tracks (default: 80)")
@click.option("--stride", default=1, help="Stride between tracks (default: 1)")
@click.option("--start", default=0, help="Number of the first tracks (default: 0)")
@click.option("--side", default=0, help="Side of floppy (default: 0)")
@click.option(
    "--resolution", default=960, help="Resolution of square output image (default: 960)"
)
@click.option("--linear/--polar", default=False, help="Image style (default: polar)")
@click.option(
    "--oversample", default=2, help="Increase oversampling of polar transformation"
)
@click.option(
    "--location",
    default=None,
    type=click.Path(exists=True),
    help="fluxengine decoder location information saved with --decoder.write_csv_to=",
)
@click.argument("input_file", type=click.Path(exists=True))
@click.argument("output_file", type=click.Path())
def main(
    slices,
    stacks,
    diameter,
    tracks,
    input_file,
    output_file,
    stride,
    start,
    side,
    resolution,
    linear,
    oversample,
    location,
):  # pylint: disable=redefined-builtin,too-many-arguments,too-many-locals, invalid-name, too-many-branches,too-many-statements
    """Visualize INPUT (any file readable by greaseweazle, including scp and
    KryoFlux) to OUTPUT (any file supported by skimage including png and jpg)
    """
    flux = open_flux(input_file)

    if linear:
        major = round(tracks * stacks)
    else:
        major = round(diameter * stacks / 2)

    density = render_flux(
        flux, side, tracks, start, stride, major, slices, stacks, location
    )

    if not linear:
        density = circularize(density, resolution, oversample)

    maxdensity = np.max(density)

    imsave(output_file, (density * (255 / maxdensity)).astype(np.uint8))


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
