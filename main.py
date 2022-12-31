import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__))+"/py_modules")
from typing import List
import pathlib
import asyncio
import logging
import zeroconf
import socket
import pychromecast
from pychromecast import CastBrowser, SimpleCastListener

import streamserver
from chromecast_types import CastDevice

# get plugin directory
PLUGIN_DIR = str(pathlib.Path(__file__).parent.resolve())
# set log level
logging.basicConfig(filename="/tmp/chromecast-decky.log",
                    format='[Template] %(asctime)s %(levelname)s %(message)s',
                    filemode='w+',
                    force=True)
logger = logging.getLogger()
logger.setLevel(logging.INFO) # can be changed to logging.DEBUG for debugging issues



class Plugin:
	port: int = 8069
	chromecast_browser: pychromecast.CastBrowser = None
	chromecast: pychromecast.Chromecast = None


	
	# Asyncio-compatible long-running code, executed in a task when the plugin is loaded
	async def _main(self):
		# startup
		logger.info("Initializing Chromecast Plugin")
		while True:
			await asyncio.sleep(1)
	
	# Function called first during the unload process, utilize this to handle your plugin being removed
	async def _unload(self):
		logger.info("Unloading Chromecast Plugin")
		pass
	
	
	
	# start searching for cast devices
	async def start_cast_discovery(self):
		logger.info("starting cast discovery")
		if self.chromecast_browser is None:
			zconf = zeroconf.Zeroconf()
			self.chromecast_browser = CastBrowser(
				SimpleCastListener(),
				zeroconf_instance=zconf,
				known_hosts=None)
		self.chromecast_browser.start_discovery()
		logger.info("done starting cast discovery")
	
	# get all the currently discovered cast devices
	async def get_cast_devices(self) -> List[CastDevice]:
		logger.info("getting cast devices")
		if self.chromecast_browser is None:
			return None
		devices: List[CastDevice] = []
		for cast_info in self.chromecast_browser.devices.values():
			devices.append(CastDevice(cast_info))
		logger.info("got {count} cast devices".format(count=len(devices)))
		return devices
	
	# stop searching for cast devices
	async def stop_cast_discovery(self):
		logger.info("stopping cast discovery")
		if self.chromecast_browser is None:
			return
		self.chromecast_browser.stop_discovery()
		logger.info("done stopping cast discovery")
	
	

	# get the URL of the desktop stream
	def get_stream_url(self):
		local_ip = socket.gethostbyname(socket.gethostname())
		return 'http://{local_ip}:{port}/live'.format(
			local_ip = local_ip,
			port = self.port)
	
	# start casting the desktop stream to the given chromecast
	async def start_casting(self, device: CastDevice, timeout=pychromecast.DISCOVER_TIMEOUT):
		# check if already connected to chromecast
		if self.chromecast is not None:
			if self.chromecast.uuid == device.uuid:
				# reconnect to chromecast
				self.chromecast.connect()
			else:
				# disconnect from old chromecast
				await self.stop_casting()
		# get chromecast if needed
		if self.chromecast is None:
			self.chromecast = pychromecast.get_chromecast_from_cast_info(
					device.to_namedtuple(),
					zconf=self.chromecast_browser.zc,
					timeout=timeout)
		self.chromecast.wait()
		# start desktop stream server
		if not streamserver.is_started():
			streamserver.start(port=self.port)
		# play stream on chromecast
		mc = self.chromecast.media_controller
		stream_url = self.get_stream_url()
		mc.play_media(stream_url, content_type="video/mp4", stream_type="LIVE")
		mc.block_until_active()

	# get the device that is currently being casted to
	async def get_casting_device(self) -> CastDevice:
		if self.chromecast is None:
			return None
		return CastDevice(self.chromecast.cast_info)
	
	# stop casting to the currently connected device
	async def stop_casting(self):
		if self.chromecast is None:
			return
		mc = self.chromecast.media_controller
		if mc.content_id == self.get_stream_url():
			self.chromecast.quit_app()
		self.chromecast.disconnect()
		self.chromecast = None
