import { Component } from 'react';
import { PanelSection, PanelSectionRow } from 'decky-frontend-lib';
import { PluginBackend, CastDevice } from './PluginBackend';

interface Props {
	backend: PluginBackend;
}

interface State {
	devices: Array<CastDevice>,
	castingDevice: CastDevice | null
}

export class CastDeviceList extends Component<Props, State> {
	mounted: boolean = false
	pollPromise: Promise<void> | null = null

	constructor(props: Props) {
		super(props)
		this.state = {
			devices: [],
			castingDevice: null
		};
	}

	async componentDidMount() {
		this.mounted = true;
		try {
			await this.props.backend.startCastDiscovery();
		} catch(error) {
			console.error(error);
			if(!this.mounted) {
				return;
			}
			try {
				await this.refreshCastDevices();
			} catch(error) {
				console.error(error);
			}
			if(!this.mounted) {
				return;
			}
			try {
				await this.refreshCurrentCastDevice();
			} catch(error) {
				console.error(error);
			}
			return;
		}
		this.pollPromise = this.pollForUpdates();
	}

	async componentWillUnmount() {
		this.mounted = false;
		if(this.pollPromise != null) {
			try {
				await this.pollPromise;
			} catch(error) {
				console.error(error);
			}
			this.pollPromise = null;
		}
		try {
			this.props.backend.stopCastDiscovery();
		} catch(error) {
			console.error(error);
		}
	}

	async refreshCastDevices() {
		const devices = await this.props.backend.getCastDevices();
		this.setState({
			devices: devices ?? []
		});
	}

	async refreshCurrentCastDevice() {
		const device = await this.props.backend.getCastingDevice();
		this.setState({
			castingDevice: device
		});
	}

	async pollForUpdates() {
		while(this.mounted) {
			try {
				await this.refreshCastDevices();
			} catch(error) {
				console.error(error);
			}
			if(!this.mounted) {
				break;
			}
			try {
				await this.refreshCurrentCastDevice();
			} catch(error) {
				console.error(error);
			}
			if(!this.mounted) {
				break;
			}
			await new Promise((resolve, _) => setTimeout(resolve, 1000));
		}
	}

	render() {
		return (
			<PanelSection title="Cast Devices">
				{this.state.devices.map((device) => (
					<PanelSectionRow>
						{device.friendly_name}
					</PanelSectionRow>
				))}
			</PanelSection>
		);
	}
}
