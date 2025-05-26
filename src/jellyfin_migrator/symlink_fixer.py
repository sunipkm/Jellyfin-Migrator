# %%
from __future__ import annotations
import os
from pathlib import Path
from typing import Iterable, List, Optional, Tuple
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
        return list(filter(None, out))  # type: ignore filter out the invalid paths
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
    lines = open(fname, 'r').readlines()  # Read the file
    lines = [line.rstrip() for line in lines]  # Remove trailing whitespace
    fakes = []  # List of fake paths
    reals = []  # List of real paths
    for line in lines:  # Iterate over the lines
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
            fdr, fake = convert_from_unix(fake, root=fakeroot) # type: ignore
            # Convert the real path to a Windows path
            rdr, real = convert_from_unix(real, root=realroot) # type: ignore
            # print(f'Symlink: "{fdr}:/{fake}" -> "{rdr}:/{real}"')
            fakes.append((fdr, fake))
            reals.append((rdr, real))
        else:
            print(f"Invalid line: {line}")
    return reals, fakes


def remap_symlink(
        real: Tuple[str, Path], # type: ignore
        fake: Tuple[str, Path], # type: ignore
        drive_map: dict[str, Path],
        dry_run: bool = False,
        debug: bool = True,
        overwrite: bool = False
) -> None:
    """## Remap a windows symlink to a UNIX symlink.

    ### Args:
        - `real (Tuple[str, Path])`: Real path to the symlink.
        - `fake (Tuple[str, Path])`: Path to the symlink.
        - `drive_map (dict[str, Path])`: Dictionary mapping drive letters to UNIX paths.
        - `dry_run (bool, optional)`: Dry run. Defaults to False.
        - `debug (bool, optional)`: Debug. Defaults to True.
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
    if debug or dry_run:
        print(f"Symlink: {real} -> {fake}")
    if dry_run:
        return
    if not real.exists():
        raise FileNotFoundError(f"Real path {real} does not exist")
    if fake.exists():
        if not overwrite:
            raise FileExistsError(f"Fake path {fake} already exists")
        else:
            if debug:
                print(f"Fake path {fake} already exists, overwriting")
            fake.unlink()
    fake.symlink_to(real, target_is_directory=real.is_dir())


# %%
def symlink_fixer():
    import argparse
    parser = argparse.ArgumentParser(
        description='Remap symlinks from one drive to another.')
    parser.add_argument('symlinks', type=str, help='Path to the symlink file')
    parser.add_argument('--execute', type=bool,
                        help='Apply symlinks', default=False)
    parser.add_argument('--debug', type=bool, help='Debug mode', default=True)

    args = parser.parse_args()
    # Check if the symlink file exists
    dry_run = not args.execute
    debug = args.debug
    if not os.path.exists(args.symlinks):
        raise FileNotFoundError(f"Symlink file {args.symlinks} does not exist")

    reals, fakes = import_symlinks('nipflix_symlinks.txt')
    drive_map = {
        'e': Path('/media/jellyfin/Jellyfin'),
        'f': Path('/media/jellyfin/Jellyfin2'),
        'g': Path('/media/jellyfin/Jellyfin3'),
        'h': Path('/media/jellyfin/Jellyfin4'),
    }

    for real, fake in zip(reals, fakes):
        try:
            remap_symlink(real, fake, drive_map, dry_run=dry_run, debug=debug)
        except Exception as e:
            print(f"Error: {e}")


# %%
if __name__ == '__main__':
    symlink_fixer()
