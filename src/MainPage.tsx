import {
	PanelSection,
	PanelSectionRow,
	ServerAPI,
} from "decky-frontend-lib";
import { VFC } from "react";

export const MainPage: VFC<{ serverAPI: ServerAPI }> = ({}) => {
	return (
		<PanelSection title="Panel Section">
			<PanelSectionRow>
			</PanelSectionRow>
		</PanelSection>
	);
};
