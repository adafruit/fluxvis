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

# Usage
 * `pip install fluxvis`

 * Get your flux in a greaseweazle-compatible format such as `.scp`.

 * Use a commandline like
   ```
   python -mfluxvis --tracks 35 --diameter 108 --stride 2 dos33.scp dos33.png
   ```
