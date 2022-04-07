import numpy as np
import click
from . import invpolar
from skimage.io import imsave
from greaseweazle.image.scp import SCP

@click.command()
@click.option("--slices", default=4000, help="The angular resolution of the flux in 1/revolution")
@click.option("--stacks", default=6, help="The pixel thickness of a track")
@click.option("--center", default=90, help="The pixel thickness of the central hole")
@click.option("--tracks", default=80, help="The total count of tracks")
@click.option("--stride", default=1, help="Stride between tracks")
@click.option("--start", default=0, help="Number of the first tracks")
@click.option("--side", default=0, help="Side of floppy")
@click.option("--resolution", default=960, help="Resolution of square output image")
@click.argument("input", type=click.Path(exists=True))
@click.argument("output", type=click.Path())
def main(slices, stacks, center, tracks, input, output, stride, start, side, resolution):
    """Visualize INPUT (an scp-format flux file) to OUTPUT (a png file)
    """
    flux = SCP.from_file(input)
    
    density = np.zeros((stacks*tracks+center, slices), dtype=np.float32)
    r = np.arange(slices)

    for cyl in range(0, tracks):
        t0 = center + cyl * stacks
        t1 = center + (1+cyl) * stacks - 1
        track = flux.get_track(cyl*stride+start, side)
        if track is None: continue
        track.cue_at_index()
        if not track.index_list:
            index = sum(track.list)
        else:
            index = track.index_list[0]
        index = track.index_list[0]
        indices = np.array(track.list, dtype=np.float32) * (slices/index)
        indices = np.floor(np.add.accumulate(indices))
        hi = np.searchsorted(indices, r, 'left'),
        lo = np.searchsorted(indices, r, 'right')
        density[t0:t1, :] = lo - hi

    wrapped = invpolar.warp_inverse_polar(density, output_shape=(resolution, resolution))
    maxdensity = np.max(wrapped)

    imsave(output, (wrapped * (255/maxdensity)).astype(np.uint8))

if __name__ == '__main__':
    main()
