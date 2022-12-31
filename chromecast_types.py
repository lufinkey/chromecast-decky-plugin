from typing import List
from pychromecast import CastInfo, ServiceInfo


class CastDeviceService:
	type: str
	data: str

	def __init__(self, service_info: ServiceInfo):
		self.type = service_info.type
		self.data = service_info.data
	
	def to_namedtuple(self) -> ServiceInfo:
		return ServiceInfo(self.type, self.data)

class CastDevice:
	services: List[CastDeviceService]
	uuid: str
	model_name: str
	friendly_name: str
	host: str
	port: int
	cast_type: str
	manufacturer: str

	def __init__(self, cast_info: CastInfo):
		self.services = [];
		for service_info in cast_info.services:
			self.services.append(CastDeviceService(service_info))
		self.uuid = cast_info.uuid
		self.model_name = cast_info.model_name
		self.friendly_name = cast_info.friendly_name
		self.host = cast_info.host
		self.port = cast_info.port
		self.cast_type = cast_info.cast_type
		self.manufacturer = cast_info.manufacturer
	
	def to_namedtuple(self) -> CastInfo:
		services_set=set()
		for service in self.services:
			services_set.add(service.to_namedtuple())
		return CastInfo(
			services_set,
			self.uuid,
			self.model_name,
			self.friendly_name,
			self.host,
			self.port,
			self.cast_type,
			self.manufacturer)
