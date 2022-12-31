import {
	ServerAPI,
} from 'decky-frontend-lib';
import { VFC } from 'react';
import { PluginBackend } from './PluginBackend';
import { CastDeviceList } from './CastDeviceList';

export const MainPage: VFC<{ serverAPI: ServerAPI }> = ({ serverAPI }) => {
	const backend = new PluginBackend(serverAPI);
	return (
		<CastDeviceList backend={backend}/>
	);
};
