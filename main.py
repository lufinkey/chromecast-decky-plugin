import os
import sys
PLUGIN_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(PLUGIN_DIR+"/py_modules")
import typing
import pathlib
import logging
import zeroconf
import socket
import asyncio
from uuid import UUID

import pychromecast
from pychromecast import CastBrowser, CastInfo, SimpleCastListener

sys.path.append(PLUGIN_DIR+"/backend")
import streamserver
from utils import castinfo_fromdict, castinfo_todict, get_default_audio_sink_index, get_display_resolution

# get plugin directory
PLUGIN_DIR = str(pathlib.Path(__file__).parent.resolve())
# set log level
logging.basicConfig(filename="/tmp/chromecast-decky.log",
					format='[Template] %(asctime)s %(levelname)s %(message)s',
					filemode='w+',
					force=True)
logger = logging.getLogger()
logger.setLevel(logging.INFO) # can be changed to logging.DEBUG for debugging issues
logger.info("Loading Chromecast Plugin")


# get display and port
display: str = os.getenv("DISPLAY")
if display is None:
	display = ":0"
	logger.info("falling back to display "+display)
else:
	logger.info("using display "+str(display))
port: int = 8069



# get the URL of the desktop stream
def get_stream_url():
	global port
	local_ip = socket.gethostbyname(socket.gethostname())
	return 'http://{local_ip}:{port}/live'.format(
		local_ip = local_ip,
		port = port)



class Plugin:
	cast_browser: pychromecast.CastBrowser = None
	chromecasts: typing.Dict[UUID,pychromecast.Chromecast] = dict()
	chromecast: pychromecast.Chromecast = None

	
	
	# Asyncio-compatible long-running code, executed in a task when the plugin is loaded
	async def _main(self):
		# startup
		logger.info("Initializing Chromecast Plugin")
	
	# Function called first during the unload process, utilize this to handle your plugin being removed
	async def _unload(self):
		logger.info("Unloading Chromecast Plugin")
		# stop casting and cast discovery
		try:
			await self.stop_casting()
		except:
			pass
		try:
			await self.stop_cast_discovery()
		except:
			pass
	
	
	
	# start searching for cast devices
	async def start_cast_discovery(self, tries=None, retry_wait=None, timeout=None, known_hosts=None):
		logger.info("starting cast discovery")
		try:
			if self.cast_browser is None:
				zconf = zeroconf.Zeroconf()
				chromecasts = self.chromecasts
				chromecasts.clear()
				def add_callback(uuid, service):
					cast_info = self.cast_browser.devices[uuid]
					chromecasts[uuid] = pychromecast.get_chromecast_from_cast_info(
						cast_info=cast_info,
						zconf=zconf)
					logger.info("found "+cast_info.friendly_name)
				def update_callback(uuid, service):
					cast_info = self.cast_browser.devices[uuid]
					if uuid not in chromecasts:
						chromecasts[uuid] = pychromecast.get_chromecast_from_cast_info(
							cast_info,
							zconf=zconf,
							tries=tries,
							retry_wait=retry_wait,
							timeout=timeout)
					logger.info("updated "+cast_info.friendly_name)
				def remove_callback(uuid, service, cast_info):
					if uuid in chromecasts:
						chromecasts[uuid].disconnect(blocking=False)
					chromecasts.pop(uuid)
					logger.info("removed "+cast_info.friendly_name)
				self.cast_browser = CastBrowser(
					SimpleCastListener(
						add_callback=add_callback,
						remove_callback=remove_callback,
						update_callback=update_callback),
					zeroconf_instance=zconf,
					known_hosts=known_hosts)
			self.cast_browser.start_discovery()
		except BaseException as error:
			logger.error(str(error))
			raise error
		logger.info("done starting cast discovery")
	
	# get all the currently discovered cast devices
	async def get_cast_devices(self) -> list:
		if self.cast_browser is None:
			return None
		devices = []
		try:
			for chromecast in self.chromecasts.values():
				devices.append(castinfo_todict(chromecast.cast_info))
		except BaseException as error:
			logger.error(str(error))
			raise error
		return devices
	
	# stop searching for cast devices
	async def stop_cast_discovery(self):
		logger.info("stopping cast discovery")
		try:
			if self.cast_browser is not None:
				self.cast_browser.stop_discovery()
				self.cast_browser = None
		except BaseException as error:
			logger.error(str(error))
			raise error
		logger.info("done stopping cast discovery")
	

	
	# start casting the desktop stream to the given chromecast
	async def start_casting(self, device: dict):
		global port
		global display
		logger.info("starting casting to "+device["friendly_name"]+" ("+str(device["uuid"])+")")
		try:
			device: CastInfo = castinfo_fromdict(device)
		except BaseException as error:
			logger.error(str(error))
			raise error
		# check if already connected to chromecast
		if self.chromecast is not None:
			if self.chromecast.uuid != device.uuid:
				# disconnect from old chromecast
				await self.stop_casting()
		chromecast = None
		try:
			# get chromecast if needed
			chromecast = self.chromecast
			if chromecast is None:
				for cmpChromecast in self.chromecasts.values():
					if cmpChromecast.cast_info.uuid == device.uuid:
						chromecast = cmpChromecast
						break
				if chromecast is None:
					logger.info("scanning for chromecast with uuid "+str(device.uuid))
					chromecasts, browser = pychromecast.get_listed_chromecasts(uuids=[device.uuid])
					browser.stop_discovery()
					if len(chromecasts) == 0:
						raise RuntimeError("Couldn't find chromecast "+device.friendly_name)
					chromecast = chromecasts[0]
			self.chromecast = chromecast
			# connect to chromecast
			logger.info("got chromecast, waiting to connect")
			if not chromecast.socket_client.is_alive():
				chromecast.socket_client.start()
			while not chromecast.status_event.is_set():
				await asyncio.sleep(0.2)
				if not chromecast.socket_client.is_alive():
					if self.chromecast is chromecast:
						self.chromecast = None
					raise RuntimeError("Disconnected from chromecast "+chromecast.cast_info.friendly_name)
			# start desktop stream server
			logger.info("starting desktop stream server")
			if not streamserver.is_started():
				streamserver.start(port=port)
			# play stream on chromecast
			mc = chromecast.media_controller
			stream_url = get_stream_url()
			logger.info("playing media url "+stream_url)
			mc.play_media(stream_url, content_type="video/mp4", stream_type="LIVE")
			# wait until session is active
			while not mc.session_active_event.is_set():
				await asyncio.sleep(0.2)
				if not chromecast.socket_client.is_alive() or self.chromecast is None:
					# raise RuntimeError("Disconnected from chromecast "+chromecast.cast_info.friendly_name+" while waiting to cast")
					return
			#mc.seek(6)
		except BaseException as error:
			logger.error(str(error))
			if chromecast is not None and not chromecast.socket_client.is_alive() and self.chromecast is chromecast:
				self.chromecast = None
			raise error
		logger.info("casted to device")

	# get the device that is currently being casted to
	async def get_casting_device(self) -> dict:
		if self.chromecast is None:
			return None
		elif not self.chromecast.socket_client.is_alive():
			return None
		return castinfo_todict(self.chromecast.cast_info)
	
	# stop casting to the currently connected device
	async def stop_casting(self):
		chromecast = self.chromecast
		if chromecast is not None:
			logger.info("stopping cast to "+str(chromecast.uuid))
		else:
			logger.info("stopping cast")
		# stop stream server
		try:
			streamserver.stop()
		except BaseException as error:
			logger.error(str(error))
			raise error
		# quit app
		try:
			mc = chromecast.media_controller
			if mc.status and mc.status.content_id == get_stream_url():
				chromecast.quit_app()
		except BaseException as error:
			logger.error(str(error))
		# disconnect from chromecast
		try:
			chromecast.socket_client.disconnect()
			while chromecast.socket_client.is_alive():
				await asyncio.sleep(0.2)
			if chromecast is self.chromecast:
				self.chromecast = None
		except BaseException as error:
			logger.error(str(error))
			raise error
		logger.info("stopped casting")
