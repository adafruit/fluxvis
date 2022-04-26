# SPDX-FileCopyrightText: 2022 Jeff Epler for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""Flux visualizer"""

import csv
import numpy as np
import click
from skimage.transform import downscale_local_mean
from skimage.io import imsave
from skimage.color import gray2rgb
from .greaseweazle.tools.util import get_image_class
from . import invpolar
from . import a2r_to_flux
from . import a2rchery

PHYSICAL_TRACK = "Physical track"
PHYSICAL_SIDE = "Physical side"
HEADER_START_NS = "Header start (ns)"
HEADER_END_NS = "Header end (ns)"
DATA_START_NS = "Data start (ns)"
DATA_END_NS = "Data end (ns)"
STATUS = "Status"

HEADER_COLOR = np.array((128, 128, 255), dtype=np.uint8)
DATA_OK_COLOR = np.array((128, 255, 128), dtype=np.uint8)
DATA_BAD_COLOR = np.array((255, 128, 128), dtype=np.uint8)


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
@click.argument("input", type=click.Path(exists=True))
@click.argument("output", type=click.Path())
def main(
    slices,
    stacks,
    diameter,
    tracks,
    input,
    output,
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
    if input.lower().endswith(".a2r"):
        a2r = a2rchery.A2RReader(input)
        flux = a2r_to_flux(a2r)
    else:
        loader = get_image_class(input)
        flux = loader.from_file(input)
    if linear:
        major = round(tracks * stacks)
    else:
        major = round(diameter * stacks / 2)

    density = np.zeros((major, slices), dtype=np.float32)
    r = np.arange(slices)

    track_duration = {}

    for cyl in range(0, tracks):
        t0 = major - (1 + cyl) * stacks
        t1 = major - cyl * stacks - 1
        track = flux.get_track(cyl * stride + start, side)
        if track is None:
            continue
        track.cue_at_index()
        if not track.index_list:
            index = sum(track.list)
        else:
            index = track.index_list[0]
        index = track.index_list[0]
        track_duration[cyl] = index
        indices = np.array(track.list, dtype=np.float32) * ((slices - 1) / index)
        indices = np.floor(np.add.accumulate(indices))
        lo = np.searchsorted(indices, r, "left")
        hi = np.searchsorted(indices, r, "right")
        density[t0:t1, :] = hi - lo

    def ns2loc(offset_ns, cyl_duration):
        return round(
            offset_ns * flux.sample_freq / 1_000_000_000 / cyl_duration * (slices - 1)
        )

    if location is not None:

        def paint(t0, t1, start, end, color):
            while start > slices:
                start -= slices
                end -= slices
            status[t0 : t1 + 1, start:end] = color
            if end > slices:
                status[t0 : t1 + 1, : end % slices] = color

        status = np.zeros((major, slices, 3), dtype=np.uint8) + 255
        with open(location, "r", encoding="utf-8", errors="ignore") as f:
            for row in csv.DictReader(f):
                physical_track = row.get(PHYSICAL_TRACK)
                physical_side = row.get(PHYSICAL_SIDE)
                header_start = row.get(HEADER_START_NS)
                header_end = row.get(HEADER_END_NS)
                data_start = row.get(DATA_START_NS)
                data_end = row.get(DATA_END_NS)
                data_status = row.get(STATUS)

                if any(x is None for x in (physical_track, physical_side, data_status)):
                    continue

                physical_side = int(physical_side)
                physical_track = int(physical_track)
                if physical_side != side:
                    continue
                if physical_track % stride != start:
                    continue

                cyl = (physical_track - start) // stride
                if cyl not in track_duration:
                    continue
                t0 = major - (1 + cyl) * stacks
                t1 = major - cyl * stacks - 1

                if header_start is not None and header_end is not None:
                    header_start = ns2loc(float(header_start), track_duration[cyl])
                    header_end = ns2loc(float(header_end), track_duration[cyl])
                    if data_start is not None:  # artifically enlarge header mark
                        header_end = ns2loc(float(data_start), track_duration[cyl])
                    paint(t0, t1, header_start, header_end, HEADER_COLOR)

                if data_start is not None and data_end is not None:
                    data_start = ns2loc(float(data_start), track_duration[cyl])
                    data_end = ns2loc(float(data_end), track_duration[cyl])
                    paint(
                        t0,
                        t1,
                        data_start,
                        data_end,
                        DATA_OK_COLOR if data_status == "OK" else DATA_BAD_COLOR,
                    )

        density = gray2rgb(density) * status
    if not linear:
        multichannel = len(density.shape) == 3
        density = invpolar.warp_inverse_polar(
            density,
            output_shape=(resolution * oversample, resolution * oversample),
            multichannel=multichannel,
        )
        if multichannel:
            density = downscale_local_mean(density, (oversample, oversample, 1))
        else:
            density = downscale_local_mean(density, (oversample, oversample))
    maxdensity = np.max(density)

    imsave(output, (density * (255 / maxdensity)).astype(np.uint8))


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
