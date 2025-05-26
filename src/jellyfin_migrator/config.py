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
                                     'doc': 'Mapping of source paths to target paths for migration.'})
    path_remap: dict[str, str] = field(default_factory=dict, metadata={
                                       'doc': 'Mapping of paths for filesystem replacements.'})
    log_no_warnings: bool = field(default=False, metadata={
                                  'doc': 'If True, suppresses warnings about missing path replacements.'})
    windows_root_path: str = field(
        default='C:/ProgramData/Jellyfin', metadata={'doc': 'Root path for Jellyfin on Windows.'})
    linux_root_path: str = field(default='/home/jellyfin/.jellyfin/Jellyfin',
                                 metadata={'doc': 'Root path for Jellyfin on Linux.'})

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
