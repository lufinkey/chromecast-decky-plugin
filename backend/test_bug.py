#!/usr/bin/env python3

import asyncio
import zeroconf
import pychromecast
from pychromecast import CastBrowser, SimpleCastListener

async def test_pychromecast():
	print("starting cast discovery")
	zconf = zeroconf.Zeroconf()
	chromecasts = {}
	def add_callback(uuid, service):
		cast_info = browser.devices[uuid]
		chromecasts[uuid] = pychromecast.get_chromecast_from_cast_info(
			cast_info,
			zconf=zconf)
		print("found "+cast_info.friendly_name)
	def update_callback(uuid, service):
		cast_info = browser.devices[uuid]
		chromecasts[uuid] = pychromecast.get_chromecast_from_cast_info(
			cast_info,
			zconf=zconf)
		print("updated "+cast_info.friendly_name)
	def remove_callback(uuid, service, cast_info):
		chromecasts.pop(uuid)
		print("removed "+cast_info.friendly_name)
	
	browser = CastBrowser(
		SimpleCastListener(
			add_callback=add_callback,
			remove_callback=remove_callback,
			update_callback=update_callback),
		zeroconf_instance=zconf)
	browser.start_discovery()
	await asyncio.sleep(4)
	
	chromecast: pychromecast.Chromecast = None
	for cmpChromecast in chromecasts.values():
		if cmpChromecast.cast_info.friendly_name == "Living Room TV":
			chromecast = cmpChromecast
			break
	if chromecast is None:
		print("couldn't find chromecast")
		return
	print("Connecting to "+chromecast.cast_info.friendly_name)
	chromecast.wait()
	print("Connected to "+chromecast.cast_info.friendly_name)

	mc = chromecast.media_controller
	stream_url = "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
	print("playing media url "+stream_url)
	chromecast.quit_app()
	mc.play_media(stream_url, content_type="video/mp4")
	mc.block_until_active(timeout=10.0)
	
	await asyncio.sleep(30)
	
asyncio.run(test_pychromecast())
