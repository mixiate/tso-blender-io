"""Read The Sims Online anim files."""

import dataclasses
import mathutils
import pathlib
import struct
import typing


from . import utils


@dataclasses.dataclass
class TimeProperty:
    """A time property."""

    time: int
    property_lists: list[utils.PropertyList]


def read_time_properties(file: typing.BinaryIO) -> list[TimeProperty]:
    """Read time properties from a file."""
    count = struct.unpack('>I', file.read(4))[0]
    return [
        TimeProperty(
            struct.unpack('>I', file.read(4))[0],
            utils.read_property_lists(file),
        )
        for _ in range(count)
    ]


@dataclasses.dataclass
class TimePropertyList:
    """A time property list."""

    time_properties: list[TimeProperty]


def read_time_property_lists(file: typing.BinaryIO) -> list[TimePropertyList]:
    """Read time property lists from a file."""
    count = struct.unpack('>I', file.read(4))[0]
    return [
        TimePropertyList(
            read_time_properties(file),
        )
        for _ in range(count)
    ]


@dataclasses.dataclass
class Motion:
    """An anim motion."""

    bone_name: str
    frame_count: int
    duration: float
    positions_used_flag: int
    rotations_used_flag: int
    position_offset: int
    rotation_offset: int
    property_lists: list[utils.PropertyList]
    time_property_lists: list[TimePropertyList]


def read_motion(file: typing.BinaryIO) -> Motion:
    """Read an anim motion from a file."""
    file.read(4)

    bone_name = utils.read_string(file)
    frame_count = struct.unpack('>I', file.read(4))[0]
    duration = struct.unpack('<f', file.read(4))[0]
    positions_used_flag = struct.unpack('<B', file.read(1))[0]
    rotations_used_flag = struct.unpack('<B', file.read(1))[0]
    position_offset = struct.unpack('>i', file.read(4))[0]
    rotation_offset = struct.unpack('>i', file.read(4))[0]

    has_property_lists = struct.unpack('<B', file.read(1))[0]
    property_lists = utils.read_property_lists(file) if has_property_lists else []

    has_time_property_lists = struct.unpack('<B', file.read(1))[0]
    time_property_lists = read_time_property_lists(file) if has_time_property_lists else []

    return Motion(
        bone_name,
        frame_count,
        duration,
        positions_used_flag,
        rotations_used_flag,
        position_offset,
        rotation_offset,
        property_lists,
        time_property_lists,
    )


@dataclasses.dataclass
class Anim:
    """Description of an anim file."""

    name: str
    duration: float
    distance: float
    moves: bool
    translations: list[mathutils.Vector]
    rotations: list[mathutils.Quaternion]
    motions: list[Motion]


def read_anim(file: typing.BinaryIO) -> Anim:
    """Read an anim from a file."""
    version = struct.unpack('>I', file.read(4))[0]
    if version != 0x02:
        raise utils.FileReadError

    name = utils.read_string_16_bit_length_be(file)

    duration = struct.unpack('<f', file.read(4))[0]
    distance = struct.unpack('<f', file.read(4))[0]
    moves = struct.unpack('<b', file.read(1))[0] != 0

    translation_count = struct.unpack('>I', file.read(4))[0]
    translations = [struct.unpack('<3f', file.read(12)) for _ in range(translation_count)]

    rotation_count = struct.unpack('>I', file.read(4))[0]
    rotations = [struct.unpack('<4f', file.read(16)) for _ in range(rotation_count)]

    motions_count = struct.unpack('>I', file.read(4))[0]
    motions = [read_motion(file) for _ in range(motions_count)]

    return Anim(
        name,
        duration,
        distance,
        moves,
        translations,
        rotations,
        motions,
    )


def read_file(file_path: pathlib.Path) -> Anim:
    """Read an anim file."""
    try:
        with file_path.open(mode='rb') as file:
            anim = read_anim(file)

            if len(file.read(1)) != 0:
                raise utils.FileReadError

            return anim

    except (OSError, struct.error) as exception:
        raise utils.FileReadError from exception
