import os
import subprocess
import shutil
import tempfile
import logging
import threading
import socket
from typing import Tuple
from flask import Flask, Response
from werkzeug.serving import BaseWSGIServer, make_server, prepare_socket

logger = logging.getLogger()


# -- Flask App

app = Flask(__name__)
video_dir = tempfile.gettempdir()+"/chromecast_decky_stream"
ffmpeg_proc: subprocess.Popen = None
video_resolution: Tuple[int,int] = None

'''
@app.route("/live")
def live():
	return Response(ffmpeg.run_async(ffmpeg_output).stdout, mimetype="video/mp4")
'''

@app.route('/live')
def stream():
	global ffmpeg_proc
	if ffmpeg_proc is not None:
		ffmpeg_proc.kill()
		ffmpeg_proc = None
	(video_width, video_height) = video_resolution
	ffmpeg_proc = subprocess.Popen(
		[ "ffmpeg", "-f", "x11grab", "-s", str(video_width)+"x"+str(video_height), "-i", ":0.0",
			"-vcodec", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
			"-maxrate", "10000k", "-bufsize", "20000k", "-pix_fmt", "yuv420p", "-g", "60",
			"-f", "mp4", "-max_muxing_queue_size", "9999", "-movflags", "frag_keyframe+empty_moov",
			"pipe:1"],
		#env={"DISPLAY": ":0"},
		stdout=subprocess.PIPE)
	return Response(ffmpeg_proc.stdout, mimetype="video/mp4")



# -- Server Process

server: BaseWSGIServer = None
server_thread: threading.Thread = None
server_socket_fd: int = None

def start(resolution: Tuple[int,int], host: str = "0.0.0.0", port: int = 8069):
	global server
	global server_thread
	global server_socket_fd
	global ffmpeg_proc
	global video_resolution
	(screen_w, screen_h) = resolution
	# ensure server isn't already started
	if server is not None:
		logger.error("Cannot start StreamServer multiple times")
		return
	# ensure resolution is valid
	if screen_w > 1920:
		screen_w = 1920
	if screen_h > 1080:
		screen_h = 1080
	# kill stream process if running
	if ffmpeg_proc is not None:
		ffmpeg_proc.kill()
		ffmpeg_proc = None
	# delete and re-create video directory
	if os.path.exists(video_dir):
		shutil.rmtree(video_dir)
	os.mkdir(video_dir)
	# start server process
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
	video_resolution = (screen_w, screen_h)
	server_thread = threading.Thread(target=lambda:server.serve_forever())
	server_thread.start()

def is_started() -> bool:
	return server_thread is not None

def stop():
	global server
	global server_thread
	global server_socket_fd
	global ffmpeg_proc
	if server is not None:
		server.shutdown()
	if server_thread is not None:
		server_thread.join()
		server_thread = None
		server = None
	if server_socket_fd is not None:
		os.close(server_socket_fd)
		server_socket_fd = None
	# delete video directory
	if os.path.exists(video_dir):
		shutil.rmtree(video_dir)
