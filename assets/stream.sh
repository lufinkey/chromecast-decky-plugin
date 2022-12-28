OBS_FOLDER="obs-studio"

mkdir -p "$OBS_FOLDER"
cd "$OBS_FOLDER"
if [ ! -e "obs" ]; then
	ln -s "$(which obs)" obs
fi
cd "$OBS_FOLDER"
obs --portable --startstreaming --minimize-to-tray

