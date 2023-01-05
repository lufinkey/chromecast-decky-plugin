#!/bin/sh
set -e
function runas_deck() {
        runuser -l deck -c "export XDG_RUNTIME_DIR=/run/user/1000; $1"
}
audio_device_index=$(runas_deck "pactl list sinks short" | head -n1 | awk '{print $1;}')
if [ -n "$audio_device_index" ]; then
    echo "got audio device index $audio_device_index" >&2
	ffmpeg_audio_args="-f pulse -ac 2 -i $audio_device_index"
else
	echo "creating silent audio track as fallback for missing audio device" >&2
	ffmpeg_audio_args="-f wav -i anullsrc"
fi
runas_deck "ffmpeg -loglevel warning -thread_queue_size 256 $ffmpeg_audio_args -f wav pipe:1" | \
ffmpeg -loglevel warning -thread_queue_size 256 -framerate 60 -device /dev/dri/card0 -f kmsgrab -i - -thread_queue_size 256 -f wav -i pipe:0 -vaapi_device /dev/dri/renderD128 -vf 'hwmap=derive_device=vaapi,scale_vaapi=format=nv12' -vcodec h264_vaapi -bf 1 -f mpegts pipe:1 | \
ffmpeg -loglevel warning -f mpegts -i pipe: -vcodec libx264 -preset ultrafast -tune zerolatency -maxrate 10000k -bufsize 20000k -vf format=pix_fmts=yuv420p -g 60 -f mp4 -max_muxing_queue_size 9999 -movflags frag_keyframe+empty_moov pipe:1
