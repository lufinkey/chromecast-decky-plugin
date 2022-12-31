import os
import sys
PLUGIN_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(PLUGIN_DIR+"/py_modules")
import pathlib
import logging
import zeroconf
import socket
import pychromecast
from pychromecast import CastBrowser, CastInfo, SimpleCastListener

sys.path.append(PLUGIN_DIR+"/backend")
import streamserver
from chromecast_types import castinfo_fromdict, castinfo_todict

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



class Plugin:
	port: int = 8069
	chromecast_browser: pychromecast.CastBrowser = None
	chromecast: pychromecast.Chromecast = None


	
	# Asyncio-compatible long-running code, executed in a task when the plugin is loaded
	async def _main(self):
		# startup
		logger.info("Initializing Chromecast Plugin")
	
	# Function called first during the unload process, utilize this to handle your plugin being removed
	async def _unload(self):
		logger.info("Unloading Chromecast Plugin")
		pass
	
	
	
	# start searching for cast devices
	async def start_cast_discovery(self):
		logger.info("starting cast discovery")
		if self.chromecast_browser is not None:
			await self.stop_cast_discovery()
			self.chromecast_browser = None
		zconf = zeroconf.Zeroconf()
		self.chromecast_browser = CastBrowser(
			SimpleCastListener(),
			zeroconf_instance=zconf,
			known_hosts=None)
		self.chromecast_browser.start_discovery()
		logger.info("done starting cast discovery")
	
	# get all the currently discovered cast devices
	async def get_cast_devices(self) -> list:
		logger.info("getting cast devices")
		if self.chromecast_browser is None:
			return None
		devices = []
		for cast_info in self.chromecast_browser.devices.values():
			devices.append(castinfo_todict(cast_info))
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
	async def get_stream_url(self):
		local_ip = socket.gethostbyname(socket.gethostname())
		return 'http://{local_ip}:{port}/live'.format(
			local_ip = local_ip,
			port = self.port)
	
	# start casting the desktop stream to the given chromecast
	async def start_casting(self, device: dict, timeout=pychromecast.DISCOVER_TIMEOUT):
		device: CastInfo = castinfo_fromdict(device)
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
	async def get_casting_device(self) -> dict:
		if self.chromecast is None:
			return None
		return castinfo_todict(self.chromecast.cast_info)
	
	# stop casting to the currently connected device
	async def stop_casting(self):
		if self.chromecast is None:
			return
		mc = self.chromecast.media_controller
		if mc.content_id == self.get_stream_url():
			self.chromecast.quit_app()
		self.chromecast.disconnect()
		self.chromecast = None
