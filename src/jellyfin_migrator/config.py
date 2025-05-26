from pathlib import Path
from dataclasses import dataclass, field
from fancy_dataclass import TOMLDataclass

@dataclass
class MigrationConfig(TOMLDataclass):
    windows_ffmpeg_path: str = field(metadata={'doc': 'Path to the ffmpeg executable on Windows.'})
    linux_ffmpeg_path: str = field(metadata={'doc': 'Path to the ffmpeg executable on Linux.'})
    path_map: dict[str, str] = field(default_factory=dict, metadata={'doc': 'Mapping of source paths to target paths for migration.'})
    path_remap: dict[str, str] = field(default_factory=dict, metadata={'doc': 'Mapping of paths for filesystem replacements.'})
    log_no_warnings: bool = field(default=False, metadata={'doc': 'If True, suppresses warnings about missing path replacements.'})
    windows_root_path: str = field(default='C:/ProgramData/Jellyfin', metadata={'doc': 'Root path for Jellyfin on Windows.'})
    linux_root_path: str = field(default='/home/jellyfin/.jellyfin/Jellyfin', metadata={'doc': 'Root path for Jellyfin on Linux.'})

    def get_path_replacements(self)->dict[str, str]:
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
    
    def get_fs_path_replacements(self)->dict[str, str]:
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
        

# # TODO BEFORE YOU START:
# # * Create a copy of the jellyfin database you want to migrate
# # * Delete the following temp/cache folders (resp. the matching
# #   folders for your installation)
# #   * C:/ProgramData/Jellyfin/Server/cache
# #   * C:/ProgramData/Jellyfin/Server/log
# #   * C:/ProgramData/Jellyfin/Server/data/subtitles
# #     Note: this only contains *cached* subtitles that have been
# #           extracted on-the-fly from files streamed to clients.
# #   * RTFM (read the README.md) and you're ready to go.
# #   * Careful when replacing everything in your new installation,
# #     you might want to *not* copy your old network settings
# #     (C:/ProgramData/Jellyfin/Server/config/networking.xml)

# # Please specify a log file. The script is rather verbose and important
# # errors might get lost in the process. You should definitely check the
# # log file after running the script to see if there are any warnings or
# # other important messages! Use f.ex. notepad++ (npp) to quickly
# # highlight and remove bunches of uninteresting log messages:
# #   * Open log file in npp
# #   * Go to "Search -> Mark... (CTRL + M)"
# #   * Tick "Bookmark Line"
# #   * Search for strings that (only!) occur in the lines you want to
# #     remove. All those lines should get a marking next to the line number.
# #   * Go to "Search -> Bookmark -> Remove Bookmarked Lines"
# #   * Repeat as needed
# # Text encoding is UTF-8 (in npp selectable under "Encoding -> UTF-8")
# log_file = "D:/jf-migrator.log"
# JELLYFIN_LNX_PATH = '/home/jellyfin/.jellyfin/Jellyfin'

# # These paths will be processed in the order they're listed here.
# # This can be very important! F.ex. if specific subfolders go to a different
# # place than stuff in the root dir of a given path, the subfolders must be
# # processed first. Otherwise, they'll be moved to the same place as the other
# # stuff in the root folder.
# # Note: all the strings below will be converted to Path objects, so it doesn't
# # matter whether you write / or \\ or include a trailing / . After the path
# # replacement it will be converted back to a string with slashes as specified
# # by target_path_slash.
# # Note2: The AppDataPath and MetadataPath entries are only there to make sure
# # the script recognizes them as actual paths. This is necessary to adjust
# # the (back)slashes as specified. This can only be done on "known" paths
# # because (back)slashes occur in other strings, too, where they must not be
# # changed.
# path_replacements = {
#     # Self-explanatory, I guess. "\\" if migrating *to* Windows, "/" else.
#     "target_path_slash": "/",
#     # Andriy's Music
#     "H:/YouTube/Andriy_Music/Set_1": "/media/jellyfin/Jellyfin4/YouTube/Andriy_Music/Set_1",
#     # Animated Shows
#     "E:/Movies/TV_Animated_Sets/Set_1": "/media/jellyfin/Jellyfin/Movies/TV_Animated_Sets/Set_1",
#     "E:/Movies/TV_Animated_Sets/Set_2": "/media/jellyfin/Jellyfin/Movies/TV_Animated_Sets/Set_2",
#     "F:/Movies/TV_Series_Sets/Animated_Set_4": "/media/jellyfin/Jellyfin2/Movies/TV_Series_Sets/Animated_Set_4",
#     "F:/Movies/TV_Series_Sets/Animated_Set_5": "/media/jellyfin/Jellyfin2/Movies/TV_Series_Sets/Animated_Set_5",
#     "G:/Movies/TV_Series_Sets/Animated_Set_6": "/media/jellyfin/Jellyfin3/Movies/TV_Series_Sets/Animated_Set_6",
#     "H:/Movies/TV_Series_Sets/Animated_Set_7": "/media/jellyfin/Jellyfin4/Movies/TV_Series_Sets/Animated_Set_7",
#     # Bangla Ekok Natok
#     "F:/Movies/TV_Movie_Sets": "/media/jellyfin/Jellyfin2/Movies/TV_Movie_Sets",
#     # Books
#     "H:/Books/Set_1": "/media/jellyfin/Jellyfin4/Books/Set_1",
#     # Coke Studio Bangla
#     "E:/YouTube/Coke Studio Bangla": "/media/jellyfin/Jellyfin/YouTube/Coke Studio Bangla",
#     "H:/Coke Studio Bangla/Season 3": "/media/jellyfin/Jellyfin4/Coke Studio Bangla/Season 3",
#     # Copa America 2021
#     "F:/FCA2021": "/media/jellyfin/Jellyfin2/FCA2021",
#     # FIFA World Cup 2022
#     "F:/FCA2022": "/media/jellyfin/Jellyfin2/FCA2022",
#     # Cooking Help
#     "H:/YouTube/Cooking Recipes": "/media/jellyfin/Jellyfin4/YouTube/Cooking Recipes",
#     # Lost & Rare Recipes
#     "H:/YouTube/Lost and Rare Recipes/Set_1": "/media/jellyfin/Jellyfin4/YouTube/Lost and Rare Recipes/Set_1",
#     # Movies
#     "E:/Movies/Films_Sets": "/media/jellyfin/Jellyfin/Films_Sets",
#     "F:/Movies/Films_Sets": "/media/jellyfin/Jellyfin2/Films_Sets",
#     "G:/Movies/Films_Sets": "/media/jellyfin/Jellyfin3/Films_Sets",
#     "H:/Movies/Films_Sets": "/media/jellyfin/Jellyfin4/Films_Sets",
#     # RHCP Live Shows
#     "F:/RHCP Live": "/media/jellyfin/Jellyfin2/RHCP Live",
#     # Russian Language Movies
#     "F:/Movies/Russian_Movies": "/media/jellyfin/Jellyfin2/Movies/Russian_Movies",
#     "H:/Movies/Russian_Movies": "/media/jellyfin/Jellyfin4/Movies/Russian_Movies",
#     # Soccer
#     "F:/Soccer": "/media/jellyfin/Jellyfin2/Soccer",
#     # Top Gear
#     "G:/Movies/Top Gear": "/media/jellyfin/Jellyfin3/Top Gear",
#     # TV Shows
#     "E:/Movies/TV_Series_Sets/Set_1": "/media/jellyfin/Jellyfin/Movies/TV_Series_Sets/Set_1",
#     "E:/Movies/TV_Series_Sets/Set_2": "/media/jellyfin/Jellyfin/Movies/TV_Series_Sets/Set_2",
#     "E:/Movies/TV_Series_Sets/Set_3": "/media/jellyfin/Jellyfin/Movies/TV_Series_Sets/Set_3",
#     "F:/Movies/TV_Series_Sets/Set_4": "/media/jellyfin/Jellyfin2/Movies/TV_Series_Sets/Set_4",
#     "F:/Movies/TV_Series_Sets/Set_5": "/media/jellyfin/Jellyfin2/Movies/TV_Series_Sets/Set_5",
#     "F:/Movies/TV_Series_Sets/Set_6": "/media/jellyfin/Jellyfin2/Movies/TV_Series_Sets/Set_6",
#     "F:/Movies/TV_Series_Sets/Set_7": "/media/jellyfin/Jellyfin2/Movies/TV_Series_Sets/Set_7",
#     "F:/Movies/TV_Series_Sets/Set_8": "/media/jellyfin/Jellyfin2/Movies/TV_Series_Sets/Set_8",
#     "G:/Movies/TV_Series_Sets/Set_9": "/media/jellyfin/Jellyfin3/Movies/TV_Series_Sets/Set_9",
#     "H:/Movies/TV_Series_Sets/Set_10": "/media/jellyfin/Jellyfin4/Movies/TV_Series_Sets/Set_10",
#     # YouTube Collections
#     "F:/YouTube Collection/Set_1": "/media/jellyfin/Jellyfin2/YouTube Collection/Set_1",
#     "G:/YouTube Collection/Set_2": "/media/jellyfin/Jellyfin3/YouTube Collection/Set_2",
#     "H:/YouTube/Set_3": "/media/jellyfin/Jellyfin4/YouTube/Set_3",

#     # Paths to the different parts of the jellyfin database. Determine these
#     # by comparing your existing installation with the paths in your new
#     # installation.
#     "C:/ProgramData/Jellyfin/config": f"{JELLYFIN_LNX_PATH}/config",
#     "C:/ProgramData/Jellyfin/cache": f"{JELLYFIN_LNX_PATH}/cache",
#     "C:/ProgramData/Jellyfin/log": f"{JELLYFIN_LNX_PATH}/log",
#     "C:/ProgramData/Jellyfin": f"{JELLYFIN_LNX_PATH}/data",
#     "C:/ProgramData/Jellyfin/transcodes": f"{JELLYFIN_LNX_PATH}/transcodes",
#     "C:/Program Files/Jellyfin/Server/ffmpeg.exe": "/usr/lib/jellyfin-ffmpeg/ffmpeg",
#     "%MetadataPath%": "%MetadataPath%",
#     "%AppDataPath%": "%AppDataPath%",
# }


# # This additional replacement dict is required to convert from the paths docker
# # shows to jellyfin back to the actual file system paths to figure out where
# # the files shall be copied. If relative paths are provided, the replacements
# # are done relative to target_root.
# #
# # Even if you're not using docker or not using path mapping with docker,
# # you probably do need to add some entries for accessing the media files
# # and appdata/metadata files. This is because the script must read all the
# # file creation and modification dates *as seen by jellyfin*.
# # In that case and if you're sure that this list is 100% correct,
# # *and only then* you can set "log_no_warnings" to True. Otherwise your logs
# # will be flooded with warnings that it couldn't find an entry to modify the
# # paths (which in that case would be fine because no modifications are needed).
# #
# # If you actually don't need any of this (f.ex. running the script in the
# # same environment as jellyfin), remove all entries except for
# #   * "log_no_warnings" (again, can be set to true if you're sure)
# #   * "target_path_slash"
# #   * %AppDataPath%
# #   * %MetadataPath%.
# fs_path_replacements = {
#     "log_no_warnings": True,
#     "target_path_slash": "/",
#     f"{JELLYFIN_LNX_PATH}": "/",
#     "%AppDataPath%": "/data/data",
#     "%MetadataPath%": "/data/metadata",
# }


# # Original root only needs to be filled if you're using auto target paths _and_
# # if your source dir doesn't match the source paths specified above in
# # path_replacements.
# # auto target will first replace source_root with original_root in a given path
# # and then do the replacement according to the path_replacements dict.
# # This is required if you copied your jellyfin DB to another location and then
# # start processing it with this script.
# original_root = Path("C:/ProgramData/Jellyfin/")
# source_root = Path("D:/Jellyfin_20250525/")
# target_root = Path("D:/Jellyfin_20250525_linux")
