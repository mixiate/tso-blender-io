"""Export The Sims Online mesh files."""

import bpy
import logging
import math
import pathlib

from . import mesh
from . import utils


MAX_VERTEX_GROUP_COUNT = 2


def export_mesh(
    logger: logging.Logger,
    output_directory: pathlib.Path,
    mesh_object: bpy.types.Object,
) -> None:
    """Export a mesh file."""
    if mesh_object.parent is None or mesh_object.parent.type != 'ARMATURE':
        logger.info(f"Skipping {mesh_object.name} as it is not parented to an armature")  # noqa: G004
        return

    mesh_data = mesh_object.data
    uv_layer = mesh_data.uv_layers[0]

    new_vertices = []
    new_faces = []

    # create unique vertices and faces
    for triangle in mesh_data.loop_triangles:
        face = []
        for loop_index in triangle.loops:
            vertex_index = mesh_data.loops[loop_index].vertex_index

            if len(mesh_data.vertices[vertex_index].groups) == 0:
                logger.info(f"{mesh_object.name} mesh has vertices that are not in a vertex group")  # noqa: G004
                return

            if len(mesh_data.vertices[vertex_index].groups) > MAX_VERTEX_GROUP_COUNT:
                logger.info(f"{mesh_object.name} mesh has vertices in more than 2 vertex groups")  # noqa: G004
                return

            vertex = (
                mesh_data.vertices[vertex_index].co,
                mesh_data.loops[loop_index].normal,
                uv_layer.data[loop_index].uv,
                mesh_data.vertices[vertex_index].groups[0].group,
                mesh_data.vertices[vertex_index].groups[1]
                if len(mesh_data.vertices[vertex_index].groups) > 1
                else None,
            )

            if vertex not in new_vertices:
                new_vertices.append(vertex)

            vertex_index = new_vertices.index(vertex)
            face.append(vertex_index)

        new_faces.append(face)

    bones: list[str] = []
    bone_bindings: list[mesh.BoneBinding] = []
    uvs: list[tuple[float, float]] = []
    blends: list[mesh.Blend] = []
    vertices: list[mesh.Vertex] = []
    blended_vertices: list[mesh.Vertex] = []

    armature = mesh_object.parent.data

    vertex_index_map = []

    # create main vertices
    for vertex_group in mesh_object.vertex_groups:
        vertex_group_vertices = []
        vertex_group_uvs = []

        armature_bone = armature.bones.get(vertex_group.name)
        if armature_bone is None:
            logger.info(
                f"Vertex group {0} in {1} is not a bone in armature {2}",  # noqa: G004
                vertex_group.name,
                mesh_object.name,
                mesh_object.parent.name,
            )
            return

        bone_matrix = (armature_bone.matrix_local @ utils.BONE_ROTATION_OFFSET_INVERTED).inverted()
        normal_bone_matrix = bone_matrix.to_quaternion().to_matrix().to_4x4()

        for vertex_index, vertex in enumerate(new_vertices):
            if vertex_group.index == vertex[3]:
                vertex_position = (bone_matrix @ vertex[0]) * utils.BONE_SCALE
                vertex_normal = normal_bone_matrix @ vertex[1]
                vertex_group_vertices.append(mesh.Vertex(vertex_position.xzy, vertex_normal.xzy))

                vertex_uvs = (vertex[2][0], -vertex[2][1])
                vertex_group_uvs.append(vertex_uvs)

                vertex_index_map.append(vertex_index)

        bone_bindings.append(
            mesh.BoneBinding(
                len(bones),
                len(vertices),
                len(vertex_group_vertices),
                0,
                0,
            ),
        )
        bones.append(vertex_group.name)

        vertices += vertex_group_vertices
        uvs += vertex_group_uvs

    # create blended vertices
    for vertex_group_index, vertex_group in enumerate(mesh_object.vertex_groups):
        vertex_group_vertices = []

        armature_bone = armature.bones[vertex_group.name]
        bone_matrix = (armature_bone.matrix_local @ utils.BONE_ROTATION_OFFSET_INVERTED).inverted()
        normal_bone_matrix = bone_matrix.to_quaternion().to_matrix().to_4x4()

        for vertex_index, vertex in enumerate(new_vertices):
            if vertex[4] is not None and vertex[4].group == vertex_group_index:
                vertex_position = (bone_matrix @ vertex[0]) * utils.BONE_SCALE
                vertex_normal = normal_bone_matrix @ vertex[1]
                vertex_group_vertices.append(mesh.Vertex(vertex_position.xzy, vertex_normal.xzy))

                weight = int(vertex[4].weight * math.pow(2, 15))
                blends.append(mesh.Blend(weight, vertex_index_map.index(vertex_index)))

        if len(vertex_group_vertices) > 0:
            bone_bindings[vertex_group_index].blended_vertex_index = len(blended_vertices)
            bone_bindings[vertex_group_index].blended_vertex_count = len(vertex_group_vertices)

            blended_vertices += vertex_group_vertices

    faces = [
        (
            vertex_index_map.index(face[2]),
            vertex_index_map.index(face[1]),
            vertex_index_map.index(face[0]),
        )
        for face in new_faces
    ]

    mesh_file_description = mesh.Mesh(
        bones,
        faces,
        bone_bindings,
        uvs,
        blends,
        vertices,
        blended_vertices,
    )

    mesh.write_file(output_directory / (mesh_object.name + ".mesh"), mesh_file_description)
