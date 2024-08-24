"""Read The Sims Online skel files."""

import dataclasses
import mathutils
import pathlib
import struct
import typing

from . import utils


@dataclasses.dataclass
class Bone:
    """A skel bone."""

    name: str
    parent: str
    property_lists: list[utils.PropertyList]
    translation: mathutils.Vector
    rotation: mathutils.Quaternion
    can_translate: int
    can_rotate: int
    can_blend: int
    wiggle_value: float
    wiggle_power: float


def read_bone(file: typing.BinaryIO) -> Bone:
    """Read a skel bone from a file."""
    file.read(4)

    name = utils.read_string(file)
    parent = utils.read_string(file)

    has_property_lists = struct.unpack('B', file.read(1))[0]
    property_lists = utils.read_property_lists(file) if has_property_lists else []

    translation = mathutils.Vector(struct.unpack('<3f', file.read(12))).xzy

    rotation = struct.unpack('<4f', file.read(16))
    rotation = mathutils.Quaternion(
        (
            rotation[3],
            rotation[0],
            rotation[2],
            rotation[1],
        ),
    )

    can_translate = struct.unpack('>I', file.read(4))[0]
    can_rotate = struct.unpack('>I', file.read(4))[0]
    can_blend = struct.unpack('>I', file.read(4))[0]

    wiggle_value = struct.unpack('<f', file.read(4))[0]
    wiggle_power = struct.unpack('<f', file.read(4))[0]

    return Bone(
        name,
        parent,
        property_lists,
        translation,
        rotation,
        can_translate,
        can_rotate,
        can_blend,
        wiggle_value,
        wiggle_power,
    )


@dataclasses.dataclass
class Skel:
    """A skel."""

    name: str
    bones: list[Bone]


def read_skel(file: typing.BinaryIO) -> Skel:
    """Read a skel from a file."""
    version = struct.unpack('>I', file.read(4))[0]
    if version != 1:
        raise utils.FileReadError

    name = utils.read_string(file)

    bone_count = struct.unpack('>H', file.read(2))[0]
    bones = [read_bone(file) for _ in range(bone_count)]

    return Skel(name, bones)


def read_file(file_path: pathlib.Path) -> Skel:
    """Read a skel file."""
    try:
        with file_path.open(mode='rb') as file:
            skel = read_skel(file)

            if len(file.read(1)) != 0:
                raise utils.FileReadError

            return skel

    except (OSError, struct.error) as exception:
        raise utils.FileReadError from exception
