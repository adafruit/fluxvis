# Flux Visualize

![VIsualization of Apple DOS 3.3 floppy as mastered by fluxengine](dos33.png)

# Usage
 * Use a virtualenv / venv if desired

 * `pip install -r requirements.txt`

 * Clone/download [greaseweazle](https://github.com/keirf/greaseweazle) and add `.../greaseweazle/scripts` to PYTHONPATH.

 * Get your flux in `.scp` format.

 * Use a commandline like
   ```
   python -mfluxvis --tracks 35 --stride 2 dos33.scp dos33.png
   ```
