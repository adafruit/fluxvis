# SPDX-FileCopyrightText: 2022 Jeff Epler for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""Helper function for use in Jupyter Notebook"""

import io
import os
import tempfile
import shutil
from ipywidgets import FileUpload
from IPython.display import display
import matplotlib.pyplot as plt
from . import open_flux, process


def go(
    side=0,
    tracks=35,
    start=0,
    stride=4,
    linear=False,
    slices=800,
    stacks=3,
    location=None,
    diameter=108,
    resolution=900,
    oversample=2,
):
    """Main helper function for operation in a notebook"""
    uploader = FileUpload(accept=".a2r,.scp", multiple=False)

    display(uploader)

    def on_upload_change(_):
        try:
            for meta, content in zip(uploader.metadata, uploader.data):
                print(f"processing {meta['name']} with content of {len(content)} bytes")
                process_one_flux(meta["name"], content)
        finally:
            uploader.metadata.clear()
            uploader.data.clear()
            uploader._counter = 0

    def process_one_flux(filename, content):
        with io.BytesIO(content) as b, tempfile.NamedTemporaryFile(
            suffix=os.path.splitext(filename)[1]
        ) as t:
            shutil.copyfileobj(b, t)
            t.flush()
            flux = open_flux(t.name)
        density = process(
            flux,
            side=side,
            tracks=tracks,
            start=start,
            stride=stride,
            linear=linear,
            slices=slices,
            stacks=stacks,
            location=location,
            diameter=diameter,
            resolution=resolution,
            oversample=oversample,
        )

        fig, axis = plt.subplots()
        fig.set_dpi(96)
        fig.set_size_inches(density.shape[0] / 96, density.shape[1] / 96)
        fig.set_frameon(False)
        fig.set_tight_layout(True)
        plt.axis("off")
        axis.imshow(density)
        plt.show()

    uploader.observe(on_upload_change, names="_counter")
