"""Read and write The Sims Online mesh files."""

import dataclasses
import pathlib
import struct
import typing

from . import utils


@dataclasses.dataclass
class BoneBinding:
    """A mesh bone binding."""

    bone_index: int
    vertex_index: int
    vertex_count: int
    blended_vertex_index: int
    blended_vertex_count: int


def read_bone_binding(file: typing.BinaryIO) -> BoneBinding:
    """Read a mesh bone binding."""
    return BoneBinding(
        struct.unpack('>I', file.read(4))[0],
        struct.unpack('>I', file.read(4))[0],
        struct.unpack('>I', file.read(4))[0],
        struct.unpack('>I', file.read(4))[0],
        struct.unpack('>I', file.read(4))[0],
    )


@dataclasses.dataclass
class Blend:
    """A mesh blend."""

    weight: int
    vertex_index: int


def read_blend(file: typing.BinaryIO) -> Blend:
    """Read a mesh blend."""
    return Blend(
        struct.unpack('>I', file.read(4))[0],
        struct.unpack('>I', file.read(4))[0],
    )


@dataclasses.dataclass
class Vertex:
    """mesh File Vertex."""

    position: tuple[float, float, float]
    normal: tuple[float, float, float]


def read_vertex(file: typing.BinaryIO) -> Vertex:
    """Read a mesh vertex."""
    return Vertex(
        struct.unpack('<3f', file.read(4 * 3)),
        struct.unpack('<3f', file.read(4 * 3)),
    )


@dataclasses.dataclass
class Mesh:
    """A mesh."""

    bones: list[str]
    faces: list[tuple[int, int, int]]
    bone_bindings: list[BoneBinding]
    uvs: list[tuple[float, float]]
    blends: list[Blend]
    vertices: list[Vertex]
    blend_vertices: list[Vertex]


def read_mesh(file: typing.BinaryIO) -> Mesh:
    """Read mesh."""
    version = struct.unpack('>I', file.read(4))[0]
    if version != 0x02:
        raise utils.FileReadError

    bone_count = struct.unpack('>I', file.read(4))[0]
    bones = [utils.read_string(file) for _ in range(bone_count)]

    face_count = struct.unpack('>I', file.read(4))[0]
    faces = [struct.unpack('>3I', file.read(12)) for _ in range(face_count)]

    bone_binding_count = struct.unpack('>I', file.read(4))[0]
    bone_bindings = [read_bone_binding(file) for _ in range(bone_binding_count)]

    vertex_count = struct.unpack('>I', file.read(4))[0]

    uvs = [struct.unpack('<2f', file.read(8)) for _ in range(vertex_count)]

    blend_vertex_count = struct.unpack('>I', file.read(4))[0]

    blends = [read_blend(file) for _ in range(blend_vertex_count)]

    file.read(4)  # total vertex count

    vertices = [read_vertex(file) for _ in range(vertex_count)]

    blend_vertices = [read_vertex(file) for _ in range(blend_vertex_count)]

    return Mesh(
        bones,
        faces,
        bone_bindings,
        uvs,
        blends,
        vertices,
        blend_vertices,
    )


def read_file(file_path: pathlib.Path) -> Mesh:
    """Read a mesh file."""
    try:
        with file_path.open(mode='rb') as file:
            mesh = read_mesh(file)

            if len(file.read(1)) != 0:
                raise utils.FileReadError

            return mesh

    except (OSError, struct.error) as exception:
        raise utils.FileReadError from exception
