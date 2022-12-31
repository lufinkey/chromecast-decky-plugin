from typing import List
from pychromecast import CastInfo, ServiceInfo


def serviceinfo_todict(service_info: ServiceInfo):
	return {
		"type": service_info.type,
		"data": service_info.data
	}

def serviceinfo_fromdict(d: dict):
	return ServiceInfo(
		d["type"],
		d["data"])

def castinfo_todict(cast_info: CastInfo):
	services = list()
	for service in cast_info.services:
		services.append(serviceinfo_todict(service))
	return {
		"services": services,
		"uuid": cast_info.uuid,
		"model_name": cast_info.model_name,
		"friendly_name": cast_info.friendly_name,
		"host": cast_info.host,
		"port": cast_info.port,
		"cast_type": cast_info.cast_type,
		"manufacturer": cast_info.manufacturer
	}

def castinfo_fromdict(d: dict):
	services = set()
	for service in d["services"]:
		services.add(serviceinfo_fromdict(service))
	return CastInfo(
		services,
		d["uuid"],
		d["model_name"],
		d["friendly_name"],
		d["host"],
		d["port"],
		d["cast_type"],
		d["manufacturer"])
