"""Read and write The Sims Online anim files."""

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


def write_time_properties(file: typing.BinaryIO, time_properties: list[TimeProperty]) -> None:
    """Write time properties to a file."""
    file.write(struct.pack('>I', len(time_properties)))
    for time_property in time_properties:
        file.write(struct.pack('>I', time_property.time))
        utils.write_property_lists(file, time_property.property_lists)


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


def write_time_property_lists(file: typing.BinaryIO, time_property_lists: list[TimePropertyList]) -> None:
    """Write time property lists to a file."""
    file.write(struct.pack('>I', len(time_property_lists)))
    for time_property_list in time_property_lists:
        write_time_properties(file, time_property_list.time_properties)


@dataclasses.dataclass
class Motion:
    """An anim motion."""

    bone_name: str
    frame_count: int
    duration: float
    uses_positions: bool
    uses_rotations: bool
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
    uses_positions = struct.unpack('<B', file.read(1))[0] != 0
    uses_rotations = struct.unpack('<B', file.read(1))[0] != 0
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
        uses_positions,
        uses_rotations,
        position_offset,
        rotation_offset,
        property_lists,
        time_property_lists,
    )


def write_motion(file: typing.BinaryIO, motion: Motion) -> None:
    """Write a motion to a file."""
    file.write(struct.pack('>I', 1))
    utils.write_string(file, motion.bone_name)
    file.write(struct.pack('>I', motion.frame_count))
    file.write(struct.pack('<f', motion.duration))
    file.write(struct.pack('B', motion.uses_positions))
    file.write(struct.pack('B', motion.uses_rotations))
    file.write(struct.pack('>i', motion.position_offset))
    file.write(struct.pack('>i', motion.rotation_offset))

    file.write(struct.pack('B', len(motion.property_lists) != 0))
    if len(motion.property_lists):
        utils.write_property_lists(file, motion.property_lists)

    file.write(struct.pack('B', len(motion.time_property_lists) != 0))
    if len(motion.time_property_lists):
        write_time_property_lists(file, motion.time_property_lists)


def write_translation(file: typing.BinaryIO, translation: mathutils.Vector) -> None:
    """Write a translation to a file."""
    file.write(struct.pack('<3f', *translation.xzy))


def write_rotation(file: typing.BinaryIO, rotation: mathutils.Quaternion) -> None:
    """Write a rotation to a file."""
    file.write(struct.pack('<f', rotation.x))
    file.write(struct.pack('<f', rotation.z))
    file.write(struct.pack('<f', rotation.y))
    file.write(struct.pack('<f', rotation.w))


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


def write_anim(file: typing.BinaryIO, animation: Anim) -> None:
    """Write an anim to a file."""
    file.write(struct.pack('>I', 0x02))

    utils.write_string_16_bit_length_be(file, animation.name)

    file.write(struct.pack('<f', animation.duration))
    file.write(struct.pack('<f', animation.distance))
    file.write(struct.pack('B', animation.moves))

    file.write(struct.pack('>I', len(animation.translations)))
    for translation in animation.translations:
        write_translation(file, translation)

    file.write(struct.pack('>I', len(animation.rotations)))
    for rotation in animation.rotations:
        write_rotation(file, rotation)

    file.write(struct.pack('>I', len(animation.motions)))
    for motion in animation.motions:
        write_motion(file, motion)


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


def write_file(file_path: pathlib.Path, animation: Anim) -> None:
    """Write an anim file."""
    with file_path.open('wb') as file:
        write_anim(file, animation)
