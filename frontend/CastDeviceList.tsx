import { Component } from 'react';
import {
	PanelSection,
	PanelSectionRow,
	Button,
	ButtonItem
} from 'decky-frontend-lib';
import { FaBan } from 'react-icons/fa';
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

	async selectCastDevice(device: CastDevice) {
		try {
			await this.props.backend.startCasting(device);
		} catch(error) {
			console.error(error);
			if(this.mounted) {
				this.setState({ error });
			}
		}
	}

	async disconnectCastDevice(device: CastDevice) {
		try {
			await this.props.backend.stopCasting();
		} catch(error) {
			console.error(error);
			if(this.mounted) {
				this.setState({ error });
			}
		}
	}

	render() {
		const state = this.state;
		let devices = state.devices;
		const castingDevice = state.castingDevice;
		if(castingDevice != null && devices.findIndex((cmpDev) => (cmpDev.uuid == castingDevice.uuid)) == -1) {
			devices = [castingDevice].concat(devices);
		}
		return (
			<div>
				{state.error != null ?
					<div>{state.error.message}</div>
				: null}
				<PanelSection title={`Cast Devices (${devices.length})`}>
					{devices.map((device) => (
						(castingDevice != null && castingDevice.uuid == device.uuid) ? (
							<PanelSectionRow>
								<div>{device.friendly_name}</div>
								<Button onClick={() => this.disconnectCastDevice(device)}><FaBan/></Button>
							</PanelSectionRow>
						) : (
							<ButtonItem
								layout='below'
								bottomSeparator={'standard'}
								onClick={() => this.selectCastDevice(device)}>
								<div>
									{device.friendly_name}
								</div>
							</ButtonItem>
						)
					))}
				</PanelSection>
			</div>
		);
	}
}
