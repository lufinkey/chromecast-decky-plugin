import os
from typing import List, Tuple
import subprocess
import asyncio

from pychromecast import CastInfo, ServiceInfo
from uuid import UUID

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

def serviceinfo_todict(service_info: ServiceInfo) -> dict:
	return {
		"type": service_info.type,
		"data": service_info.data
	}

def serviceinfo_fromdict(d: dict) -> ServiceInfo:
	return ServiceInfo(
		d["type"],
		d["data"])

def castinfo_todict(cast_info: CastInfo) -> dict:
	services = list()
	for service in cast_info.services:
		services.append(serviceinfo_todict(service))
	return {
		"services": services,
		"uuid": str(cast_info.uuid),
		"model_name": cast_info.model_name,
		"friendly_name": cast_info.friendly_name,
		"host": cast_info.host,
		"port": cast_info.port,
		"cast_type": cast_info.cast_type,
		"manufacturer": cast_info.manufacturer
	}

def castinfo_fromdict(d: dict) -> CastInfo:
	services = set()
	for service in d["services"]:
		services.add(serviceinfo_fromdict(service))
	return CastInfo(
		services,
		UUID(d["uuid"]),
		d["model_name"],
		d["friendly_name"],
		d["host"],
		d["port"],
		d["cast_type"],
		d["manufacturer"])



def get_default_audio_sink_index() -> int:
	# build pactl command
	pactl_cmd = "pactl list sinks short"
	if "XDG_RUNTIME_DIR" not in os.environ:
		# get deck user UID for XDG_RUNTIME_DIR variable
		deck_uid = get_user_uid("deck")
		if deck_uid is not None:
			pactl_cmd = "export XDG_RUNTIME_DIR='/run/user/{deck_uid}'; ".format(deck_uid=deck_uid)+pactl_cmd
	pactl_cmd = 'sudo runuser -l deck -c "sh -c \\"'+pactl_cmd+'\\""'
	# call pactl command
	output = os.popen(pactl_cmd).read()
	# parse output
	output_words = output.split()
	if len(output_words) == 0:
		raise RuntimeError("Couldn't determine default sink from output \"{output}\"".format(output=output))
	return int(output_words[0])

def get_display_resolution(display: str) -> Tuple[int, int]:
	output = os.popen("export DISPLAY='"+display+"'; xdpyinfo | awk '/dimensions/{print $2}'").read()
	dimensions = output.split('x')
	if len(dimensions) != 2:
		raise RuntimeError("Couldn't determine screen resolution from output "+output)
	return (int(dimensions[0].strip()), int(dimensions[1].strip()))


def get_user_uid(user: str):
	user_id = os.popen("id -u \"{u}\"".format(u=user)).read().strip()
	if len(user_id) == 0:
		user_id = None
	return user_id

def record_display() -> subprocess.Popen:
	global PLUGIN_DIR
	# start processes
	return subprocess.Popen(
		[ PLUGIN_DIR+"/capture_screen.sh" ],
		stdout=subprocess.PIPE)
