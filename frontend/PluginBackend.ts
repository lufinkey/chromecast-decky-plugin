import {
	ServerAPI,
} from "decky-frontend-lib";

export interface CastDevice {
	uuid: string;
	friendly_name: string;
	model_name: string;
	cast_type: string;
	manufacturer: string;
}



export class PluginBackend {
	api: ServerAPI;
	
	constructor(api: ServerAPI) {
		this.api = api;
	}

	async callPluginMethod<TRes = {}, TArgs = {}>(method: string, args: TArgs): Promise<TRes> {
		const res = await this.api.callPluginMethod<TArgs,TRes>(method, args);
		if(!res.success) {
			throw new Error("Couldn't resolve result for "+method)
		}
		return res.result;
	}



	async startCastDiscovery() {
		return await this.callPluginMethod<void>("start_cast_discovery", {})
	}

	async getCastDevices(): Promise<[CastDevice] | null> {
		return await this.callPluginMethod<[CastDevice]>("get_cast_devices", {});
	}

	async stopCastDiscovery() {
		return await this.callPluginMethod<void>("stop_cast_discovery", {});
	}



	async startCasting(device: CastDevice) {
		return await this.callPluginMethod("start_casting", { device });
	}

	async getCastingDevice(): Promise<CastDevice | null> {
		return await this.callPluginMethod<CastDevice>("get_casting_device", {});
	}
	
	async stopCasting() {
		return await this.callPluginMethod("stop_casting", {});
	}
}
