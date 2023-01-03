import os
import subprocess
import shutil
import tempfile
import logging
import threading
import socket
from typing import Tuple, List
from flask import Flask, Response
from werkzeug.serving import BaseWSGIServer, make_server, prepare_socket

from utils import get_user_uid

logger = logging.getLogger()


# -- Flask App

app = Flask(__name__)
serving_ffmpeg_procs: List[subprocess.Popen] = []
serving_audio_device_index: int = None

'''
@app.route("/live")
def live():
	return Response(ffmpeg.run_async(ffmpeg_output).stdout, mimetype="video/mp4")
'''

@app.route('/live')
def stream():
	global serving_ffmpeg_procs
	global serving_audio_device_index
	logger.info("Got request to /live endpoint")
	# kill previous ffmpeg processes
	for ffmpeg_proc in serving_ffmpeg_procs:
		ffmpeg_proc.kill()
	serving_ffmpeg_procs = []
	# start new ffmpeg process
	serving_ffmpeg_procs = record_display(audio_device_index=serving_audio_device_index)
	return Response(serving_ffmpeg_procs[0].stdout, mimetype="video/mp4")



# -- Server Process

server: BaseWSGIServer = None
server_thread: threading.Thread = None
server_socket_fd: int = None

def start(host: str = "0.0.0.0", port: int = 8069, audio_device_index: int = None):
	global server
	global server_thread
	global server_socket_fd
	global serving_ffmpeg_procs
	# ensure server isn't already started
	if server is not None:
		logger.error("Cannot start StreamServer multiple times")
		return
	# kill stream processes if running
	for ffmpeg_proc in serving_ffmpeg_procs:
		ffmpeg_proc.kill()
	serving_ffmpeg_procs = []
	# start server process if needed
	if server_socket_fd is None:
		socket = prepare_socket(host, port)
		server_socket_fd = socket.fileno()
		# Silence a ResourceWarning about an unclosed socket. This object is no longer
		# used, the server will create another with fromfd.
		socket.detach()
	os.environ["WERKZEUG_SERVER_FD"] = str(server_socket_fd)
	server = make_server(
        host,
        port,
        app,
        threaded=True,
        processes=1,
        fd=server_socket_fd)
	server_thread = threading.Thread(target=lambda:run_server(server))
	server_thread.start()

def run_server(server: BaseWSGIServer):
	logger.info("starting server thread listening on "+server.host+":"+str(server.port))
	server.serve_forever()
	logger.info("server thread ended")


def is_started() -> bool:
	return server_thread is not None

def stop():
	global server
	global server_thread
	global server_socket_fd
	global serving_ffmpeg_procs
	# set server shutdown
	if server is not None:
		server.shutdown()
	# wait for server thread to end
	if server_thread is not None:
		server_thread.join()
		server_thread = None
		server = None
	# close server socket
	if server_socket_fd is not None:
		os.close(server_socket_fd)
		server_socket_fd = None
	# end ffmpeg process
	for ffmpeg_proc in serving_ffmpeg_procs:
		ffmpeg_proc.kill()
	serving_ffmpeg_procs = []



# -- FFMPEG

def record_display(audio_device_index: int = None, output: str = "pipe:1",
	stdin=None,
	stdout=subprocess.PIPE,
	stderr=None) -> List[subprocess.Popen]:
	# get screen capture ffmpeg process args (outputs to stdout as mpegts format)
	# ffmpeg_args = "ffmpeg -thread_queue_size 512 -framerate 60 -device /dev/dri/card0 -f kmsgrab -i - -vaapi_device /dev/dri/renderD128 -vf hwmap=derive_device=vaapi,scale_vaapi=format=nv12 -c:v h264_vaapi -bf 1 -f mpegts".split(' ')
	# ffmpeg_args = "ffmpeg -thread_queue_size 512 -framerate 60 -device /dev/dri/card0 -f kmsgrab -i - -vaapi_device /dev/dri/renderD128 -preset ultrafast -tune zerolatency -maxrate 10000k -bufsize 20000k -pix_fmt yuv420p -g 60 -f mp4 -max_muxing_queue_size 9999 -movflags frag_keyframe+empty_moov".split(' ')
	# ffmpeg_args = "ffmpeg -device /dev/dri/card0 -f kmsgrab -i - -vf hwmap=derive_device=vaapi,scale_vaapi=format=nv12 -c:v h264_vaapi -qp 24 -f mp4 -max_muxing_queue_size 9999 -movflags frag_keyframe+empty_moov".split(' ')
	screen_ffmpeg_args = "ffmpeg -thread_queue_size 512 -framerate 60 -device /dev/dri/card0 -f kmsgrab -i - -vaapi_device /dev/dri/renderD128 -vf hwmap=derive_device=vaapi,scale_vaapi=format=nv12 -vcodec h264_vaapi -bf 1 -f mpegts pipe:".split(' ')
	screen_envvars = os.environ.copy()
	screen_envvars["LD_PRELOAD"] = ""
	screen_envvars["QT_QPA_PLATFORM"] = "xcb"
	# get conversion ffmpeg process args (attach audio input if provided)
	ffmpeg_screen_pipe_args_str = "-f mpegts -i pipe:"
	ffmpeg_output_format_args_str = "-vcodec libx264 -preset ultrafast -tune zerolatency -maxrate 10000k -bufsize 20000k -vf format=pix_fmts=yuv420p -g 60 -f mp4 -max_muxing_queue_size 9999 -movflags frag_keyframe+empty_moov"
	if audio_device_index is not None:
		# attach audio to output process args from provided device index
		# get deck user UID for XDG_RUNTIME_DIR variable
		deck_uid = get_user_uid("deck")
		if deck_uid is None:
			deck_uid = 1000
		output_ffmpeg_cmd_str = (
			"export XDG_RUNTIME_DIR=/run/user/{uid}; ".format(uid=deck_uid)
			+ "ffmpeg "+ffmpeg_screen_pipe_args_str
			+ " -f pulse -ac 2 -i {adi} ".format(adi=audio_device_index)
			+ ffmpeg_output_format_args_str
			+ " " + output )
		output_ffmpeg_args = [ "runuser", "-l", "deck", "-c", output_ffmpeg_cmd_str ]
	else:
		# create output process args
		output_ffmpeg_args = [ 'ffmpeg' ]
		output_ffmpeg_args.extend(ffmpeg_screen_pipe_args_str.split(' '))
		output_ffmpeg_args.extend(ffmpeg_output_format_args_str.split(' '))
		output_ffmpeg_args.append(output)
	# start processes
	screen_proc = subprocess.Popen(
		screen_ffmpeg_args,
		env=screen_envvars,
		stdin=stdin,
		stdout=subprocess.PIPE,
		stderr=stderr)
	output_proc = subprocess.Popen(
		output_ffmpeg_args,
		stdin=screen_proc.stdout,
		stdout=stdout,
		stderr=stderr)
	return [output_proc, screen_proc]
