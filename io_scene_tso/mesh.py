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


def write_bone_binding(file: typing.BinaryIO, bone_binding: BoneBinding) -> None:
    """Write a bone binding to a file."""
    file.write(struct.pack('>I', bone_binding.bone_index))
    file.write(struct.pack('>I', bone_binding.vertex_index))
    file.write(struct.pack('>I', bone_binding.vertex_count))
    file.write(struct.pack('>I', bone_binding.blended_vertex_index))
    file.write(struct.pack('>I', bone_binding.blended_vertex_count))


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


def write_blend(file: typing.BinaryIO, blend: Blend) -> None:
    """Write a blend to a file."""
    file.write(struct.pack('>I', blend.weight))
    file.write(struct.pack('>I', blend.vertex_index))


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


def write_vertex(file: typing.BinaryIO, vertex: Vertex) -> None:
    """Write a vertex to a file."""
    file.write(struct.pack('<3f', *vertex.position))
    file.write(struct.pack('<3f', *vertex.normal))


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


def write_mesh(file: typing.BinaryIO, mesh: Mesh) -> None:
    """Write a mesh to a file."""
    file.write(struct.pack('>I', 0x02))

    file.write(struct.pack('>I', len(mesh.bones)))
    for bone in mesh.bones:
        utils.write_string(file, bone)

    file.write(struct.pack('>I', len(mesh.faces)))
    for face in mesh.faces:
        file.write(struct.pack('>3I', *face))

    file.write(struct.pack('>I', len(mesh.bone_bindings)))
    for bone_binding in mesh.bone_bindings:
        write_bone_binding(file, bone_binding)

    file.write(struct.pack('>I', len(mesh.vertices)))

    for uv in mesh.uvs:
        file.write(struct.pack('<2f', *uv))

    file.write(struct.pack('>I', len(mesh.blend_vertices)))

    for blend in mesh.blends:
        write_blend(file, blend)

    file.write(struct.pack('>I', len(mesh.vertices) + len(mesh.blend_vertices)))

    for vertex in mesh.vertices:
        write_vertex(file, vertex)

    for vertex in mesh.blend_vertices:
        write_vertex(file, vertex)


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


def write_file(file_path: pathlib.Path, mesh: Mesh) -> None:
    """Write a mesh file."""
    with file_path.open('wb') as file:
        write_mesh(file, mesh)
