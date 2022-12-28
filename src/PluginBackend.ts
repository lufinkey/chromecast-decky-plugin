import {
	ServerAPI,
} from "decky-frontend-lib";

export class PluginBackend {
    api: ServerAPI;
    
    constructor(api: ServerAPI) {
        this.api = api;
    }

    
}
