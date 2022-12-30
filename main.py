import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__))+"/py_modules")
import pathlib
import subprocess
import asyncio
import logging
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
    backend_proc = None
    

    # Asyncio-compatible long-running code, executed in a task when the plugin is loaded
    async def _main(self):
        # startup
        logger.info("Initializing Chromecast Plugin")
        self.backend_proc = subprocess.Popen([PLUGIN_DIR+"/bin/backend"])
        StreamServer.start()
        while True:
            await asyncio.sleep(1)

    # Function called first during the unload process, utilize this to handle your plugin being removed
    async def _unload(self):
        logger.info("Unloading Chromecast Plugin")
        pass
