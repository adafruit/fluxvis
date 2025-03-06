# SPDX-FileCopyrightText: 2022 Jeff Epler for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""Visualize floppy flux"""

import csv
import numpy as np
from skimage.color import gray2rgb
from skimage.transform import downscale_local_mean
from .greaseweazle.tools.util import get_image_class
from . import a2rchery
from . import invpolar

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


class A2RTrackShim:
    """Adapt an A2R file's track to act similar to a GreaseWeazle track"""

    def __init__(self, flux, est_index):
        self.index_list = [est_index]
        self.list = []
        append = self.list.append
        subtotal = 0
        for value in flux:
            subtotal += value
            if value < 255:
                append(value)
                subtotal = 0

    def cue_at_index(self):
        """No-operation needed for GW compatibility"""


class A2RFluxShim:
    """Adapt an A2R file to act similar to a GreaseWeazle flux file"""

    @property
    def sample_freq(self):
        """The (fixed) sample frequency of an A2R file"""
        return 8_000_000

    def __init__(self, a2r):
        self._a2r = a2r

    def get_track(self, track, side):
        """Retrieve data about a track"""
        if side == 0 and track in self._a2r.flux:
            flux = self._a2r.flux[track][0]
            return A2RTrackShim(flux["data"], flux["tick_count"])
        return A2RTrackShim([1, 1, 1, 1], 4)


def a2r_to_flux(a2r):
    """Wrap a shim around an A2R file so we can visualize it"""
    return A2RFluxShim(a2r)


def open_flux(filename):
    """Open a flux file by filename"""
    if filename.lower().endswith(".a2r"):
        a2r = a2rchery.A2RReader(filename)
        return a2r_to_flux(a2r)
    loader = get_image_class(filename)
    return loader.from_file(filename)


def render_flux(flux, side, tracks, start, stride, major, slices, stacks, location):
    """Render flux to a linear image"""
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
    return density


def circularize(density, resolution, oversample):
    """Transform a linear density image to circular"""
    multichannel = len(density.shape) == 3
    density = invpolar.warp_inverse_polar(
        density,
        output_shape=(resolution * oversample, resolution * oversample),
        multichannel=multichannel,
    )
    if multichannel:
        return downscale_local_mean(density, (oversample, oversample, 1))
    return downscale_local_mean(density, (oversample, oversample))


def process(
    flux,
    side,
    tracks,
    start,
    stride,
    linear,
    slices,
    stacks,
    location,
    diameter,
    resolution,
    oversample,
):
    """Process flux into an image"""

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
    return (density * (255 / maxdensity)).astype(np.uint8)
