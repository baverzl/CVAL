#!/bin/sh

if [ $# -ne 2 ]; then
	echo "Usage: jpeg2mp4.sh <directory where your jpegs are located>"
	exit 1
fi

dir = $1
ffmpeg -framerate 25 -i $dir/frame%04d.jpg -c:v libx264 -profile:v high -crf 20 -pix_fmt yuv420p output.mp4
