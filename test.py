#!/usr/bin/env python3

import asyncio
from main import Plugin

plugin = Plugin()

async def test_plugin(plugin: Plugin):
	print("starting cast discovery")
	await plugin.start_cast_discovery()
	await asyncio.sleep(1)

	print("getting cast devices")
	devices = await plugin.get_cast_devices()
	print("got "+str(len(devices))+" devices")
	for device in devices:
		print("device "+str(device))
	
	print ("stopping cast discovery")
	await plugin.stop_cast_discovery()
	
asyncio.run(test_plugin(plugin))
