<!--
SPDX-FileCopyrightText: 2022 Jeff Epler for Adafruit Industries

SPDX-License-Identifier: CC-BY-4.0
-->

# Flux Visualize

Produce flux visualization from any flux files recognized by greaseweazle

Visualization of a Commodore 1541 floppy as mastered by fluxengine:

<p align="center"
   
![Visualization of Commodore 1541 floppy as mastered by fluxengine](etc/disk.jpg)
</p>

# Usage
 * Use a virtualenv / venv if desired

 * `pip install -r requirements.txt`

 * Clone/download [greaseweazle](https://github.com/keirf/greaseweazle) and add `.../greaseweazle/scripts` to PYTHONPATH.

 * Get your flux in `.scp` format.

 * Use a commandline like
   ```
   python -mfluxvis --tracks 35 --stride 2 dos33.scp dos33.png
   ```
