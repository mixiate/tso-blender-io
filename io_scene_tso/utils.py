"""Utility functions and classes."""

import dataclasses
import math
import mathutils
import struct
import typing


BONE_SCALE = 3.0
BONE_ROTATION_OFFSET = mathutils.Matrix.Rotation(math.radians(-90.0), 4, 'Z')
BONE_ROTATION_OFFSET_INVERTED = BONE_ROTATION_OFFSET.inverted()


def read_string(file: typing.BinaryIO) -> str:
    """Read a pascal string from a file."""
    length = struct.unpack('B', file.read(1))[0]
    return file.read(length).decode("windows-1252")


@dataclasses.dataclass
class Property:
    """A property."""

    name: str
    value: str


def read_properties(file: typing.BinaryIO) -> list[Property]:
    """Read properties from a file."""
    count = struct.unpack('>I', file.read(4))[0]
    return [
        Property(
            read_string(file),
            read_string(file),
        )
        for _ in range(count)
    ]


@dataclasses.dataclass
class PropertyList:
    """A property list."""

    properties: list[Property]


def read_property_lists(file: typing.BinaryIO) -> list[PropertyList]:
    """Read property lists from a file."""
    count = struct.unpack('>I', file.read(4))[0]
    return [
        PropertyList(
            read_properties(file),
        )
        for _ in range(count)
    ]


class FileReadError(Exception):
    """General purpose file read error."""
