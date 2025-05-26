# %%
from __future__ import annotations
import argparse
import os
from pathlib import Path
from typing import Iterable, List, Optional, Tuple
import logging
from dataclasses import dataclass, field
from fancy_dataclass import TOMLDataclass
from tqdm import tqdm

from .argparse_override import override
# %% Define the configuration dataclass


@dataclass
class SymlinkFixerConfig(TOMLDataclass, doc_as_comment=True):
    """Configuration for the symlink fixer.

This file processes symlinks (intended to be NTFS symlinks created with `mklink` without the `/j` flag) 
found using `ls -lR /path/to/folder | grep '^l'` in WSL, and on a UNIX system, recreates them as UNIX symlinks.

`realroot` and `fakeroot` are parts of the path in the output of the `find` command that are removed from the
target and symlink paths, respectively, to resolve the Windows drive letter.

The `mapping` dictionary maps drive letters on Windows to their corresponding UNIX paths. 
"""
    mapping: dict[str, Path] = field(
        metadata={'doc': 'Mapping of drive letters to UNIX paths.'}
    )
    fakeroot: Optional[str] = field(
        default=None,
        metadata={
            'doc': 'Root path to make the fake path (symlink) relative to. Defaults to None.'}
    )
    realroot: Optional[str] = field(
        default='/mnt',
        metadata={
            'doc': 'Root path to make the real path (target) relative to. Defaults to /mnt.'}
    )


# %% Set up logging
log_formatter = logging.Formatter(
    fmt='[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
root_logger = logging.getLogger()  # get root logger
stream_handler = logging.StreamHandler()  # this is stdout/stderr
stream_handler.setLevel(logging.INFO)  # this only logs info and up
stream_handler.setFormatter(log_formatter)
root_logger.addHandler(stream_handler)  # add the log file handler
root_logger.setLevel(logging.DEBUG)  # logger handles debug and up
# %%


def convert_from_unix(fname: str | List[str], root: Optional[str] = None) -> Tuple[str, Path] | None | List[Tuple[str, Path]]:
    """Convert a UNIX path to a Windows path

    Args:
        fname (str | List[str]): String or list of strings from `find /path/to/files -links +1 2>/dev/null > /path/to/output.txt` command.
        root (Optional[str], optional): Root path to make the path relative to. Defaults to None.

    Raises:
        TypeError: Invalid input type.

    Returns:
        Path | None | List[Path]: Sanitized Windows paths, if they exist.
    """
    if isinstance(fname, str):  # If string
        if root is not None:
            # make it relative to the root
            fname = os.path.relpath(fname, root)
        parts = fname.split('/')  # Split by UNIX line ending
        drive = parts[0]  # the first part is the drive letter
        path = os.path.join('', *parts[1:])  # join all the parts
        path = Path(path)  # convert to a Path object
        return (drive, path)
    elif isinstance(fname, Iterable):
        out = [convert_from_unix(f) for f in fname]
        # filter out the invalid paths
        return list(filter(None, out))  # type: ignore
    else:
        raise TypeError(f'Unknown type {type(fname)}')


def import_symlinks(fname: str, fakeroot: Optional[str] = None, realroot: Optional[str] = '/mnt') -> Tuple[List[Tuple[str, Path]], List[Tuple[str, Path]]]:
    """## Import symlink descriptions from a file.

    ### Args:
        - `fname (str)`: Text file containing the symlink descriptions.
        - `fakeroot (Optional[str], optional)`: Root path to make the fake path relative to. Defaults to None.
        - `realroot (Optional[str], optional)`: Root path to make the real path relative to. Defaults to '/mnt'.

    ### Returns:
        - `Tuple[List[Tuple[str, Path]], List[Tuple[str, Path]]]`: Tuple of real and fake paths. Each path is a tuple of the drive letter and the path to the drive root. 
    """
    logging.info(
        f"Importing symlinks from {fname} with fakeroot={fakeroot} and realroot={realroot}")
    lines = open(fname, 'r').readlines()  # Read the file
    lines = [line.rstrip() for line in lines]  # Remove trailing whitespace
    fakes = []  # List of fake paths
    reals = []  # List of real paths
    for line in tqdm(lines, desc='Import symlinks'):  # Iterate over the lines
        # Discard the first 10 words of size, permissions, etc.
        line = line.split(maxsplit=10)[-1]
        # Split the remaining line by the symlink arrow
        words = line.split('->')
        if len(words) == 2:  # If there are two parts
            # The first part is the fake path
            fake = words[0].strip().replace('\\', '')
            # The second part is the real path
            real = words[1].strip().replace('\\', '')
            # Convert the fake path to a Windows path
            fdr, fake = convert_from_unix(fake, root=fakeroot)  # type: ignore
            # Convert the real path to a Windows path
            rdr, real = convert_from_unix(real, root=realroot)  # type: ignore
            fakes.append((fdr, fake))
            reals.append((rdr, real))
        else:
            logging.warning(f"Invalid line: {line}")
    return reals, fakes


def remap_symlink(
        real: Tuple[str, Path],  # type: ignore
        fake: Tuple[str, Path],  # type: ignore
        drive_map: dict[str, Path],
        dry_run: bool = False,
        overwrite: bool = False
) -> None:
    """## Remap a windows symlink to a UNIX symlink.

    ### Args:
        - `real (Tuple[str, Path])`: Real path to the symlink.
        - `fake (Tuple[str, Path])`: Path to the symlink.
        - `drive_map (dict[str, Path])`: Dictionary mapping drive letters to UNIX paths.
        - `dry_run (bool, optional)`: Dry run. Defaults to False.
        - `overwrite (bool, optional)`: Actually remove the NTFS symlink. Defaults to False.

    ### Raises:
        - `ValueError`: Drive letter not in drive map.
        - `FileNotFoundError`: Real path does not exist.
        - `FileExistsError`: Fake path already exists.
    """
    rdr, real = real
    fdr, fake = fake
    # Check if the drive letter is in the drive map
    if rdr.lower() in drive_map:
        # If it is, remap the path to the new drive letter
        real = drive_map[rdr] / real
    else:
        raise ValueError(f"Drive letter {rdr} not in drive map")
    # Check if the drive letter is in the drive map
    if fdr.lower() in drive_map:
        # If it is, remap the path to the new drive letter
        fake = drive_map[fdr] / fake
    else:
        raise ValueError(f"Drive letter {fdr} not in drive map")
    real: Path = real
    fake: Path = fake
    # Check if the real path exists
    if dry_run:
        logging.info(f"Symlink: {real} -> {fake}")
        return
    if not real.exists():
        raise FileNotFoundError(f"Real path {real} does not exist")
    os.system(f'rm "{fake}"')
    if fake.exists():
        if not overwrite:
            raise FileExistsError(f"Fake path {fake} already exists")
        else:
            logging.debug(f"Fake path {fake} already exists, overwriting")
    os.system(f'ln -s "{real}" "{fake}"')

# %% Class to handle the generate command line argument


def generate_config(values: Path) -> None:
    config = SymlinkFixerConfig(mapping={'a': Path('/media/user/path_a')})
    loc = Path(values)  # type: ignore
    if loc.exists():  # type: ignore
        logging.error(
            f"Configuration file {values} already exists. Please remove it before generating a new one.")
        return
    with open(loc, 'w') as f:
        config.to_toml(f)
    logging.info(f"Generated configuration file at {loc}")


# %%
def symlink_fixer():
    import argparse
    parser = argparse.ArgumentParser(
        description='Remap symlinks from one drive to another.')
    parser.add_argument(
        'symlinks', type=str, help='Path to the database mapping (broken) NTFS symlinks to correct UNIX paths')
    parser.add_argument('config', type=Path,
                        help='Path to the configuration TOML file')
    parser.add_argument('--execute',
                        help='Apply symlinks', default=False, action='store_true')
    parser.add_argument('--debug', type=str,
                        help='Debug mode [DEBUG | INFO | WARNING | ERROR]', default='WARNING')
    parser.add_argument('--logfile', type=str,
                        help='Log file path', default='symlink_fixer.log')
    parser.add_argument('--generate', type=Path, action=override(generate_config), default=None,
                        help='Generate a blank configuration file')
    # Parse the arguments
    args = parser.parse_args()
    # Check if the symlink file exists
    dry_run = not args.execute
    # Set up logging
    log_file_handle = logging.FileHandler(
        args.logfile, mode='w', encoding='utf8', errors='surrogateescape')  # log file
    log_file_handle.setLevel(logging.DEBUG)  # set it to debug and up
    log_file_handle.setFormatter(log_formatter)
    root_logger.addHandler(log_file_handle)  # add the log file handler
    # Set up console logging level
    if args.debug.upper() == 'DEBUG':
        stream_handler.setLevel(logging.DEBUG)
    elif args.debug.upper() == 'INFO':
        stream_handler.setLevel(logging.INFO)
    elif args.debug.upper() == 'WARNING':
        stream_handler.setLevel(logging.WARNING)
    elif args.debug.upper() == 'ERROR':
        stream_handler.setLevel(logging.ERROR)
    else:
        raise ValueError(f"Unknown debug level: {args.debug}")
    if not os.path.exists(args.symlinks):
        raise FileNotFoundError(f"Symlink file {args.symlinks} does not exist")
    if not os.path.exists(args.config):
        raise FileNotFoundError(f"Config file {args.config} does not exist")
    # Load the configuration
    with open(args.config, 'r') as f:
        # Load the configuration from the TOML file
        logging.info(f"Loading configuration from {args.config}")
        config = SymlinkFixerConfig.from_toml(f)

    reals, fakes = import_symlinks(
        args.symlinks, config.fakeroot, config.realroot)

    for real, fake in tqdm(zip(reals, fakes), total=len(reals), desc='Creating symlinks'):
        try:
            remap_symlink(real, fake, config.mapping, dry_run=dry_run, overwrite=True)
        except Exception as e:
            # Log the error without newlines
            logging.warning(f"{e}".replace('\n', ' '))


# %%
if __name__ == '__main__':
    symlink_fixer()
