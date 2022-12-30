import {
	definePlugin,
	ServerAPI,
	staticClasses,
} from "decky-frontend-lib";
import { FaChromecast } from "react-icons/fa";
import { MainPage } from "./MainPage";

export default definePlugin((serverApi: ServerAPI) => {
	/*serverApi.routerHook.addRoute('/some-plugin-test-page', DeckyPluginRouterTest, {
		exact: true,
	});*/
	
	return {
		title: <div className={staticClasses.Title}>Example Plugin</div>,
		content: <MainPage serverAPI={serverApi} />,
		icon: <FaChromecast/>,
		onDismount() {
			//serverApi.routerHook.removeRoute('/some-plugin-test-page');
		},
	};
});
