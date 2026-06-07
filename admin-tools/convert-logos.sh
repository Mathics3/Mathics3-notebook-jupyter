#!/bin/bash
# Convert SVG logo to 32x32-logo.png and 64x64-logo.png
# for use in Jupyter
bs=${BASH_SOURCE[0]}
mydir=$(dirname $bs)
cd $mydir/../static
convert -background none -resize 32x32 logo-heptatom.svg logo-32x32.png
convert -background none -resize 64x64 logo-heptatom.svg logo-64x64.png
