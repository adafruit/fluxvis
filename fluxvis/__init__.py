# SPDX-FileCopyrightText: 2022 Jeff Epler for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""Visualize floppy flux"""

from .greaseweazle.tools.util import get_image_class
from . import a2rchery


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
