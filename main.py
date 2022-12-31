import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__))+"/py_modules")
import pathlib
import asyncio
import logging
import zeroconf
import socket
import pychromecast
from pychromecast import CastBrowser, SimpleCastListener
from .backend import StreamServer

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
	
	

	async def start_cast_discovery(self):
		if self.chromecast_browser is None:
			zconf = zeroconf.Zeroconf()
			self.chromecast_browser = CastBrowser(SimpleCastListener(),
				zeroconf_instance=zconf,
				known_hosts=None)
		self.chromecast_browser.start_discovery()
	
	async def get_cast_devices(self):
		if self.chromecast_browser is None:
			return list()
		return list(self.chromecast_browser.devices.values())
	
	async def stop_cast_discovery(self):
		if self.chromecast_browser is None:
			return
		self.chromecast_browser.stop_discovery()
	
	
	
	def get_stream_url(self):
		local_ip = socket.gethostbyname(socket.gethostname())
		return 'http://'+local_ip+'/live'
	
	async def start_casting(self, device, timeout=pychromecast.DISCOVER_TIMEOUT):
		if self.chromecast is not None:
			if self.chromecast.uuid == device.uuid:
				self.chromecast.connect()
			else:
				self.chromecast.disconnect()
				self.chromecast = None
		if self.chromecast is None:
			self.chromecast = pychromecast.get_chromecast_from_cast_info(
					device,
					zconf=self.chromecast_browser.zc,
					timeout=timeout)
		self.chromecast.wait()
		if not StreamServer.is_started():
			StreamServer.start()
		mc = self.chromecast.media_controller
		stream_url = self.get_stream_url()
		mc.play_media(stream_url, content_type="video/mp4", stream_type="LIVE")
		mc.block_until_active()
	
	async def get_casting_uuid(self):
		if self.chromecast is None:
			return None
		return self.chromecast.uuid
	
	async def stop_casting(self):
		if self.chromecast is None:
			return
		mc = self.chromecast.media_controller
		if mc.content_id == self.get_stream_url():
			self.chromecast.quit_app()
		self.chromecast.disconnect()
		self.chromecast = None
