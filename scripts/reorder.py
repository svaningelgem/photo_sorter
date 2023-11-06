#!env python
import itertools
import json
import logging
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from functools import cached_property
from pathlib import Path
from typing import Optional, Union

import exifread
from PIL import Image, UnidentifiedImageError
from PIL.ExifTags import TAGS
from exifread.heic import NoParser
from pillow_heif import register_heif_opener

from scripts.common import is_same_file

register_heif_opener()

DEBUG = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@dataclass
class ConverterImage:
    def __init__(self, root: str | Path, filename: str | Path):
        self.root = Path(root).resolve().absolute()
        self.filename = Path(filename).resolve().absolute()

    @cached_property
    def img(self) -> Image:
        return Image.open(self.filename)

    @cached_property
    def metadata(self) -> dict:
        extra = {
            k: v
            for k, v in self.img.info.items()
            if k not in ('exif', ) and v
        }

        # assert 'metadata' not in extra, f"{self.filename} doesn't have metadata?"

        try:
            exif_data = self.img.getexif() or {}
            exif_data = {TAGS.get(k, k): v for k, v in exif_data.items()}
        except UnidentifiedImageError:
            exif_data = {}

        try:
            with open(self.filename, 'rb') as fp:
                exif_tags = {
                    k: v.values for k, v in exifread.process_file(fp, details=False).items()
                }
        except NoParser:
            exif_tags = {}

        final = {}
        final.update({str(k).lower(): v for k, v in extra.items()})
        final.update({str(k).lower(): v for k, v in exif_data.items()})
        final.update({str(k).lower(): v for k, v in exif_tags.items()})

        return final

    @cached_property
    def icc_profile(self) -> bytes:
        return self.metadata.pop('icc_profile', None)

    @cached_property
    def datetime_(self) -> datetime:
        for possible in ['datetimeoriginal', 'datetime', 'datetimedigitized']:
            for value in [v for k, v in self.metadata.items() if possible in k]:
                return datetime.strptime(value, '%Y:%m:%d %H:%M:%S')

        raise ValueError(f"No datetime found in {self.filename}")

    @cached_property
    def target_filename(self) -> Path:
        return self.root / self.datetime_.strftime(f"%Y-%m/IMG_%Y%m%d_%H%M%S{self.filename.suffix}")

    @cached_property
    def source_filename(self) -> Path:
        return self.filename

    def move(self):
        source = self.source_filename.resolve().absolute()
        source_hash = Path(str(source) + '.hash')
        target = self.target_filename.resolve().absolute()

        for counter in itertools.count():
            if counter > 0:
                new_target = target.with_stem(target.stem + f'_{counter}')
            else:
                new_target = target

            if source == new_target:  # Same location?
                return

            if not new_target.exists():
                new_target.parent.mkdir(mode=0o0755, parents=True, exist_ok=True)

                logger.debug("Moving %s -> %s", source, new_target)
                if not DEBUG:
                    source.rename(new_target)
                    if source_hash.exists():
                        new_target_hash = Path(str(new_target) + '.hash')
                        source_hash.rename(new_target_hash)
                return

            if is_same_file(source, new_target):
                # Same file
                logger.debug(f"Source %s is the same as target %s. Removing source", source, new_target)
                if not DEBUG:
                    source.unlink()
                    if source_hash.exists():
                        source_hash.unlink()
                return


class ConverterMovie(ConverterImage):
    @cached_property
    def metadata(self) -> dict:
        output = subprocess.run(["ffprobe", "-hide_banner", "-i", str(self.filename), "-print_format", "json", "-show_format", "-show_streams"], capture_output=True)
        output.check_returncode()
        return json.loads(output.stdout)

    @cached_property
    def datetime_(self) -> datetime:
        def recursive(data: dict, search: str) -> Optional[str]:
            if not isinstance(data, dict):
                raise ValueError("Not a dict")

            for k, v in data.items():
                if str(k).lower() == search:
                    return v

                try:
                    return recursive(v, search)
                except ValueError:
                    ...

            return None

        for possible_tag in ["creation_time"]:
            value = recursive(self.metadata, str(possible_tag).lower())
            if not value:
                continue

            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")

        raise ValueError(f"No datetime could be found for {self.filename}")

    @cached_property
    def target_filename(self) -> Path:
        return self.root / self.datetime_.strftime(f"%Y-%m/MOV_%Y%m%d_%H%M%S{self.filename.suffix}")


class ConverterThm(ConverterImage):
    ...


class ConverterAvi(ConverterMovie):
    @cached_property
    def _thm(self) -> ConverterThm:
        # Find .THM file
        search_for = self.filename.stem.lower() + '.thm'
        for possible_thm_file in self.filename.parent.glob("*.*"):
            if possible_thm_file.name.lower() == search_for:
                return ConverterThm(self.root, possible_thm_file)

        raise ValueError(f"No THM file found for {self.filename}... How do I find the datetime now?")

    @cached_property
    def metadata(self) -> dict:
        return self._thm.metadata

    @cached_property
    def datetime_(self) -> datetime:
        return self._thm.datetime_

    def move(self):
        super().move()
        self._thm.move()


class ConverterDeleteFile(ConverterImage):
    def move(self) -> None:
        logger.debug("Will delete %s", self.filename)
        if not DEBUG:
            self.filename.unlink()


class ConverterIgnoreFile(ConverterImage):
    def move(self) -> None:
        ...


class ConverterMov(ConverterMovie):
    ...


class ConverterPng(ConverterImage):
    def move(self):
        ...


class ConverterMp4(ConverterMovie):
    ...


class Converter3gp(ConverterMovie):
    ...


class ConverterGif(ConverterImage):
    def move(self):
        ...


class ConverterTiff(ConverterImage):
    ...


class ConverterHeic(ConverterImage):
    @cached_property
    def datetime_(self) -> datetime:
        try:
            return super().datetime_
        except AssertionError:
            logger.warning("%s has no metadata, returning file datetime", self.filename)

            stat_ = self.filename.stat()
            earliest_time = min(
                time
                for possible_time in ['st_atime', 'st_mtime', 'st_ctime']
                if (time := getattr(stat_, possible_time, 0)) > 0
            )

            return datetime.fromtimestamp(earliest_time)


conversion_list: dict[str, type[ConverterImage]] = {
    # Images
    '.jpg': ConverterImage,
    '.jpeg': ConverterImage,
    '.heic': ConverterHeic,
    '.png': ConverterPng,
    '.gif': ConverterGif,
    '.tiff': ConverterTiff,
    '.tif': ConverterTiff,
    # Extra info
    '.aae': ConverterDeleteFile,  # https://www.howtogeek.com/747946/what-are-aae-files-from-an-iphone-and-can-i-delete-them/ [AAE = XML files with edits from iPhone]
    '.thm': ConverterIgnoreFile,
    '.log': ConverterIgnoreFile,
    '.py': ConverterIgnoreFile,
    '.pdf': ConverterIgnoreFile,
    '.txt': ConverterIgnoreFile,
    '.hash': ConverterIgnoreFile,
    # Movies
    '.avi': ConverterAvi,
    '.mov': ConverterMov,
    '.mp4': ConverterMp4,
    '.3gp': Converter3gp,
}


def process_directory(directory: Union[str, Path]) -> None:
    p: Path = Path(directory).resolve().absolute()
    logger.debug("Processing %s", p)
    assert p.exists(), f"{p} does not exist?"
    assert p.is_dir(), f"{p} is not a directory?"

    all_entries = sorted(p.rglob('*.*'))
    all_dirs = set()
    try:
        for file in all_entries:
            all_dirs.add(file.parent)

            try:
                converter_class = conversion_list[file.suffix.lower()]
                converter_class(p, file).move()
            except Exception as ex:
                logger.error("[%s] %s >> %s", ex.__class__.__name__, file, ex)
    except KeyboardInterrupt:
        ...

    try:
        all_dirs.remove(p)
    except KeyError:
        ...

    for d in all_dirs.copy():
        try:
            d.rmdir()
        except OSError:
            ...


if __name__ == '__main__':
    for path_to_reorganize in sys.argv[1:]:
        process_directory(path_to_reorganize)
