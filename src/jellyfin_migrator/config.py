import logging
from pathlib import Path
from dataclasses import dataclass, field
from fancy_dataclass import TOMLDataclass


@dataclass
class MigrationConfig(TOMLDataclass):
    """
    Configuration for Jellyfin migration.

    Read the README.md for more information on how to use this configuration.
    """
    windows_ffmpeg_path: str = field(
        metadata={'doc': 'Path to the ffmpeg executable on Windows.'})
    linux_ffmpeg_path: str = field(
        metadata={'doc': 'Path to the ffmpeg executable on Linux.'})
    path_map: dict[str, str] = field(default_factory=dict, metadata={
                                     'doc': 'Mapping of source paths to target paths for migration.\n'
                                     '# These paths will be processed in the order they\'re listed here.\n'
                                     '# This can be very important! F.ex. if specific subfolders go to a different\n'
                                     '# place than stuff in the root dir of a given path, the subfolders must be\n'
                                     '# processed first. Otherwise, they\'ll be moved to the same place as the other\n'
                                     '# stuff in the root folder.\n'
                                     '# Note: all the strings below will be converted to\n'
                                     '# Path objects, so it doesn\'t matter whether you write / or \\\\ or include\n'
                                     '# a trailing / . After the path replacement it will be converted back to a string\n'
                                     '# with slashes as specified by target_path_slash.\n'
                                     '# Note2: The AppDataPath and MetadataPath entries are only there to make sure\n'
                                     '# the script recognizes them as actual paths. This is necessary to adjust \n'
                                     '# the (back)slashes as specified. This can only be done on "known" paths \n'
                                     '# because (back)slashes occur in other strings, too, where they must not be \n'
                                     '# changed.'})
    path_remap: dict[str, str] = field(default_factory=dict, metadata={
                                       'doc': 'Mapping of paths for filesystem replacements.\n'
                                       '# This additional replacement dict is required to convert from the paths docker\n'
                                       '# shows to jellyfin back to the actual file system paths to figure out where\n'
                                       '# the files shall be copied. If relative paths are provided, the replacements\n'
                                       '# are done relative to target_root.\n'
                                       '# \n'
                                       '# Even if you\'re not using docker or not using path mapping with docker,\n'
                                       '# you probably do need to add some entries for accessing the media files\n'
                                       '# and appdata/metadata files, especially if you are running the script on\n'
                                       '# a different computer. This is because the script must read all the\n'
                                       '# file creation and modification dates *as seen by jellyfin*.\n'
                                       '# In that case and if you\'re sure that this list is 100% correct,\n'
                                       '# *and only then* you can set "log_no_warnings" to True. Otherwise your logs\n'
                                       '# will be flooded with warnings that it couldn\'t find an entry to modify the\n'
                                       '# paths (which in that case would be fine because no modifications are needed).'
                                       })
    log_no_warnings: bool = field(default=False, metadata={
                                  'doc': 'If True, suppresses warnings about missing path replacements (read path_remap doc).'})
    windows_root_path: str = field(
        default='C:/ProgramData/Jellyfin', metadata={'doc': 'Original root path for Jellyfin configuration on Windows.\n'
                                                     '# Defaults to C:/ProgramData/Jellyfin, which is the default\n'
                                                     '# location for Jellyfin on Windows.'})
    linux_root_path: str = field(default='/home/jellyfin/.jellyfin/Jellyfin',
                                 metadata={'doc': 'Intended root path for Jellyfin on Linux.\n'
                                           '# Defaults to /home/jellyfin/.jellyfin/Jellyfin.'})

    def _get_path_replacements(self) -> dict[str, str]:
        base_path_replacements = {
            "target_path_slash": "/",
            f"{self.windows_root_path}/config": f"{self.linux_root_path}/config",
            f"{self.windows_root_path}/cache": f"{self.linux_root_path}/cache",
            f"{self.windows_root_path}/log": f"{self.linux_root_path}/log",
            f"{self.windows_root_path}": f"{self.linux_root_path}/data",
            f"{self.windows_root_path}/transcodes": f"{self.linux_root_path}/transcodes",
            f"{self.windows_ffmpeg_path}": f"{self.linux_ffmpeg_path}",
            "%MetadataPath%": "%MetadataPath%",
            "%AppDataPath%": "%AppDataPath%",
        }
        path_replacements = self.path_map.copy()
        path_replacements.update(base_path_replacements)
        return path_replacements

    def _get_fs_path_replacements(self) -> dict[str, str]:
        base_replacements = {
            "log_no_warnings": self.log_no_warnings,
            "target_path_slash": "/",
            f"{self.linux_root_path}": "/",
            "%AppDataPath%": "/data/data",
            "%MetadataPath%": "/data/metadata",
        }
        fs_path_replacements = self.path_remap.copy()
        fs_path_replacements.update(base_replacements)
        return fs_path_replacements


def generate_default(path: Path) -> None:
    """Generates a default configuration file at the specified path."""
    config = MigrationConfig(
        windows_ffmpeg_path="C:/Program Files/ffmpeg/bin/ffmpeg.exe",
        linux_ffmpeg_path="/usr/lib/jellyfin-ffmpeg/ffmpeg",
        path_map={
            "E:/Videos": "/home/jellyfin/Videos",
            "E:/Music": "/home/jellyfin/Music",
            "F:/Pictures": "/home/jellyfin/Pictures",
        },
        path_remap={

        },
        log_no_warnings=False,
    )
    if path.exists():
        logging.error(f"Configuration file already exists at {path}.")
    with open(path, 'w') as f:
        config.to_toml(f)
    logging.info(f"Default configuration written to {path}")


if __name__ == '__main__':
    config = MigrationConfig(
        windows_ffmpeg_path="C:/Program Files/ffmpeg/bin/ffmpeg.exe",
        linux_ffmpeg_path="/usr/lib/jellyfin-ffmpeg/ffmpeg",
        path_map={
            "E:/Videos": "/home/jellyfin/Videos",
            "E:/Music": "/home/jellyfin/Music",
            "F:/Pictures": "/home/jellyfin/Pictures",
        },
        path_remap={},
        log_no_warnings=False,
    )
    with open('migration_config.toml', 'w') as f:
        config.to_toml(f)
