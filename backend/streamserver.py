import os
import subprocess
import shutil
import tempfile
import logging
import multiprocessing
from flask import Flask, Response

logger = logging.getLogger()


# -- Flask App

app = Flask(__name__)
video_dir = tempfile.gettempdir()+"/chromecast_decky_stream"
ffmpeg_proc: subprocess.Popen = None

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
	ffmpeg_proc = subprocess.Popen(
		[ "ffmpeg", "-f", "x11grab", "-s", "1920x1200", "-i", ":0.0",
			"-vcodec", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
			"-maxrate", "10000k", "-bufsize", "20000k", "-pix_fmt", "yuv420p", "-g", "60",
			"-flush_packets", "1", "-f", "mp4", "-max_muxing_queue_size", "9999", "-movflags", "frag_keyframe+empty_moov",
			"pipe:1"],
		stdout=subprocess.PIPE)
	return Response(ffmpeg_proc.stdout, mimetype="video/mp4")



# -- Server Process

server_process: multiprocessing.Process = None

def start(host: str = "0.0.0.0", port: int = 8069):
	global server_process
	global ffmpeg_proc
	# ensure server isn't already started
	if server_process is not None:
		logger.error("Cannot start StreamServer multiple times")
		return
	# kill stream process if running
	if ffmpeg_proc is not None:
		ffmpeg_proc.kill()
		ffmpeg_proc = None
	# delete and re-create video directory
	if os.path.exists(video_dir):
		shutil.rmtree(video_dir)
	os.mkdir(video_dir)
	# start server process
	server_process = multiprocessing.Process(target=lambda:app.run(host=host, port=port))
	server_process.start()

def is_started() -> bool:
	return server_process is not None

def stop():
	global server_process
	if server_process is not None:
		server_process.terminate()
		server_process.join()
		server_process = None
	if ffmpeg_proc is not None:
		ffmpeg_proc.kill()
		ffmpeg_proc = None
	# delete video directory
	if os.path.exists(video_dir):
		shutil.rmtree(video_dir)
