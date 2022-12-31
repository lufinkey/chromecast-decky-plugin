import { Component } from 'react';
import { PanelSection, PanelSectionRow } from 'decky-frontend-lib';
import { PluginBackend, CastDevice } from './PluginBackend';

interface Props {
	backend: PluginBackend;
}

interface State {
	devices: Array<CastDevice>,
	castingDevice: CastDevice | null,
	error: any
}

export class CastDeviceList extends Component<Props, State> {
	mounted: boolean = false
	refreshPromise: Promise<void> | null = null

	constructor(props: Props) {
		super(props)
		this.mounted = false;
		this.refreshPromise = null;
		
		this.state = {
			devices: [],
			castingDevice: null,
			error: null
		};
	}

	async componentDidMount() {
		this.mounted = true;
		console.log("starting cast device discovery");
		try {
			await this.props.backend.startCastDiscovery();
		} catch(error) {
			console.error(error);
			this.refreshCastInfo();
			return;
		}
		this.pollForUpdates();
	}

	async componentWillUnmount() {
		this.mounted = false;
		console.log("stopping cast device discovery");
		try {
			this.props.backend.stopCastDiscovery();
		} catch(error) {
			console.error(error);
		}
	}

	async refreshCastDevices() {
		console.log("refreshing cast devices");
		const devices = await this.props.backend.getCastDevices();
		this.setState({
			devices: devices ?? []
		});
	}

	async refreshCurrentCastDevice() {
		console.log("refreshing current cast device");
		const device = await this.props.backend.getCastingDevice();
		this.setState({
			castingDevice: device
		});
	}

	async refreshCastInfo() {
		if(this.refreshPromise != null) {
			return await this.refreshPromise;
		}
		this.refreshPromise = (async () => {
			if(!this.mounted) {
				return;
			}
			try {
				await this.refreshCastDevices();
			} catch(error) {
				console.error(error);
				if(this.mounted) {
					this.setState({ error });
				}
			}
			if(!this.mounted) {
				return;
			}
			try {
				await this.refreshCurrentCastDevice();
			} catch(error) {
				console.error(error);
				if(this.mounted) {
					this.setState({ error });
				}
			}
			if(!this.mounted) {
				return;
			}
		})();
		try {
			await this.refreshPromise;
		} finally {
			this.refreshPromise = null;
		}
	}
	
	async pollForUpdates() {
		console.log("starting poll for chromecast updates")
		while(this.mounted) {
			await this.refreshCastInfo();
			if(!this.mounted) {
				break;
			}
			await new Promise((resolve, _) => setTimeout(resolve, 1000));
		}
		console.log("stopping poll for chromecast updates");
	}

	render() {
		return (
			<div>
				{this.state.error != null ?
					<div>{this.state.error.message}</div>
				: null}
				<PanelSection title={`Cast Devices (${this.state.devices.length})`}>
					{this.state.devices.map((device) => (
						<PanelSectionRow>
							{device.friendly_name}
						</PanelSectionRow>
					))}
				</PanelSection>
			</div>
		);
	}
}
