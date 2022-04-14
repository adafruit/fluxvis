<!--
SPDX-FileCopyrightText: 2022 Jeff Epler for Adafruit Industries

SPDX-License-Identifier: CC-BY-4.0
-->

# Flux Visualize

Produce flux visualization from any flux files recognized by greaseweazle

Visualization of a Commodore 1541 floppy as mastered by fluxengine:

<p align="center"
   
![Visualization of Commodore 1541 floppy as mastered by fluxengine](https://github.com/adafruit/fluxvis/raw/main/etc/disk.jpg)
</p>

When a fluxengine-style CSV file with decoder information is supplied, the interpretation of each portion of the disk is shown:
<p align="center"
   
![Colors show interpretation of disk structure](https://github.com/adafruit/fluxvis/raw/main/etc/diskcolor.jpg)
</p>

 * Blue: metadata
 * Green: successfully decoded data
 * Red: data could not be decoded

# Usage
 * `pip install fluxvis`

 * Get your flux in a greaseweazle-compatible format such as `.scp` or in the ".a2r" format.

 * Use a commandline like
   ```
   python -mfluxvis --tracks 35 --diameter 108 --stride 2 dos33.scp dos33.png
   ```
