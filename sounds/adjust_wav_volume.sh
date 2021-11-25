#!/bin/bash
echo "increase all wav file volume by 8 dB"
shopt -s globstar
output="/tmp/output_louder.wav"
for i in **/*.wav; do # Whitespace-safe and recursive
    ffmpeg -y -i "$i" -filter:a volume=8dB "$output"
    mv "$output" "$i"
done
