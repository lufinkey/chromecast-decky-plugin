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

from utils import record_display

logger = logging.getLogger()


# -- Flask App

app = Flask(__name__)
serving_capture_proc: subprocess.Popen = None
serving_audio_device_index: int = None

'''
@app.route("/live")
def live():
	return Response(ffmpeg.run_async(ffmpeg_output).stdout, mimetype="video/mp4")
'''

@app.route('/live')
def stream():
	global serving_capture_proc
	global serving_audio_device_index
	logger.info("Got request to /live endpoint")
	# kill previous ffmpeg process
	if serving_capture_proc is not None:
		serving_capture_proc.kill()
		serving_capture_proc = None
	# start new ffmpeg process
	serving_capture_proc = record_display()
	return Response(serving_capture_proc.stdout, mimetype="video/mp4")



# -- Server Process

server: BaseWSGIServer = None
server_thread: threading.Thread = None
server_socket_fd: int = None

def start(host: str = "0.0.0.0", port: int = 8069, audio_device_index: int = None):
	global server
	global server_thread
	global server_socket_fd
	global serving_capture_proc
	# ensure server isn't already started
	if server is not None:
		logger.error("Cannot start StreamServer multiple times")
		return
	# kill stream process if running
	if serving_capture_proc is not None:
		serving_capture_proc.kill()
		serving_capture_proc = None
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
	global serving_capture_proc
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
	if serving_capture_proc is not None:
		serving_capture_proc.kill()
		serving_capture_proc = None
