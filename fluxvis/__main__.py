# SPDX-FileCopyrightText: 2022 Jeff Epler for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""Flux visualizer"""

import click
from skimage.io import imsave
import matplotlib.pyplot as plt
from . import open_flux, process


@click.group()
@click.pass_context
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
def main(
    ctx,
    side,
    tracks,
    start,
    stride,
    slices,
    stacks,
    location,
    diameter,
    resolution,
    linear,
    oversample,
):
    """Commandline interface to visualize flux"""
    ctx.ensure_object(dict)
    ctx.obj.update(
        {
            "side": side,
            "tracks": tracks,
            "start": start,
            "stride": stride,
            "linear": linear,
            "slices": slices,
            "stacks": stacks,
            "location": location,
            "diameter": diameter,
            "resolution": resolution,
            "oversample": oversample,
        }
    )


@main.command()
@click.pass_context
@click.argument("input_file", type=click.Path(exists=True))
def view(ctx, input_file):
    """Render a flux image to the screen

    INPUT_FILE may be any flux format recognized by the embedded copy of
    greaseweazle (.scp, etc) or an a2r file."""
    flux = open_flux(input_file)
    density = process(flux, **ctx.obj)

    fig, axis = plt.subplots()
    fig.set_dpi(96)
    fig.set_size_inches(density.shape[0] / 96, density.shape[1] / 96)
    fig.set_frameon(False)
    fig.set_tight_layout(True)
    plt.axis("off")
    axis.imshow(density)
    plt.show()


@main.command()
@click.pass_context
@click.argument("input_file", type=click.Path(exists=True))
@click.argument("output_file", type=click.Path())
def write(ctx, input_file, output_file):
    """Render a flux image to a file

    INPUT_FILE may be any flux format recognized by the embedded copy of
    greaseweazle (.scp, etc) or an a2r file.

    OUTPUT_FILE may be any image format recognized by scikit_img including PNG,
    GIF, and JPG"""
    flux = open_flux(input_file)
    density = process(flux, **ctx.obj)
    imsave(output_file, density)


if __name__ == "__main__":
    main()
