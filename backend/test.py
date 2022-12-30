
import time
import pychromecast
import StreamServer

# List chromecasts on the network, but don't connect
services, browser = pychromecast.discovery.discover_chromecasts()
# Shut down discovery
pychromecast.discovery.stop_discovery(browser)

# Discover and connect to chromecasts named Living Room
chromecasts, browser = pychromecast.get_listed_chromecasts(friendly_names=["Luis's Alt Bedroom TV"])

cast = chromecasts[0]
# Start worker thread and wait for cast device to be ready
cast.wait()
cast.quit_app()

StreamServer.start(host="0.0.0.0", port=8069)

time.sleep(1)

#'''
mc = cast.media_controller
mc.play_media('http://192.168.1.105:8069/live', content_type="video/mp4", stream_type="LIVE")
mc.block_until_active()
time.sleep(5)
mc.play()
print(mc.status)
#'''

time.sleep(60)
