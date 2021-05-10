for f in *.m4a; do ffmpeg -i "$f" "${f/%m4a/wav}"; done
