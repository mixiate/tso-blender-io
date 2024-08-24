"""Import The Sims Online mesh files."""

import bmesh
import bpy
import logging
import math
import mathutils
import pathlib

from . import mesh
from . import utils


def import_mesh(
    context: bpy.types.Context,
    logger: logging.Logger,
    file_path: pathlib.Path,
    armature_object: bpy.types.Object,
) -> bpy.types.Object | None:
    """Import a mesh file."""
    mesh_desc = mesh.read_file(file_path)

    armature = armature_object.data

    if not all(bone in armature.bones for bone in mesh_desc.bones):
        logger.info(
            f"Could not apply mesh {file_path.stem} to armature {armature_object.name}. The bones do not match.",  # noqa: G004
        )
        return None

    obj_mesh = bpy.data.meshes.new(file_path.stem)
    obj = bpy.data.objects.new(file_path.stem, obj_mesh)

    context.collection.objects.link(obj)

    b_mesh = bmesh.new()

    normals = []
    deform_layer = b_mesh.verts.layers.deform.verify()

    for bone_binding in mesh_desc.bone_bindings:
        bone_name = mesh_desc.bones[min(bone_binding.bone_index, len(mesh_desc.bones) - 1)]

        armature_bone = armature.bones[bone_name]
        bone_matrix = armature_bone.matrix_local @ utils.BONE_ROTATION_OFFSET_INVERTED

        vertex_group = obj.vertex_groups.new(name=bone_name)

        vertex_index_start = bone_binding.vertex_index
        vertex_index_end = vertex_index_start + bone_binding.vertex_count
        for vertex in mesh_desc.vertices[vertex_index_start:vertex_index_end]:
            position = mathutils.Vector(vertex.position).xzy / utils.BONE_SCALE
            b_mesh_vertex = b_mesh.verts.new(bone_matrix @ position)

            bone_matrix_normal = bone_matrix.to_quaternion().to_matrix().to_4x4()
            normal = bone_matrix_normal @ mathutils.Vector(vertex.normal).xzy
            normals.append(normal)

            b_mesh_vertex[deform_layer][vertex_group.index] = 1.0

    b_mesh.verts.ensure_lookup_table()
    b_mesh.verts.index_update()

    for bone_binding in mesh_desc.bone_bindings:
        bone_name = mesh_desc.bones[min(bone_binding.bone_index, len(mesh_desc.bones) - 1)]
        vertex_group = obj.vertex_groups[bone_name]

        blend_index_start = bone_binding.blended_vertex_index
        blend_index_end = blend_index_start + bone_binding.blended_vertex_count
        for blend in mesh_desc.blends[blend_index_start:blend_index_end]:
            for inner_bone_binding in mesh_desc.bone_bindings:
                vertex_index_start = inner_bone_binding.vertex_index
                vertex_index_end = vertex_index_start + inner_bone_binding.vertex_count
                if blend.vertex_index >= vertex_index_start and blend.vertex_index < vertex_index_end:
                    original_bone_name = mesh_desc.bones[inner_bone_binding.bone_index]

            original_vertex_group = obj.vertex_groups[original_bone_name]
            weight = float(blend.weight) * math.pow(2, -15)
            b_mesh.verts[blend.vertex_index][deform_layer][original_vertex_group.index] = 1 - weight
            b_mesh.verts[blend.vertex_index][deform_layer][vertex_group.index] = weight

    invalid_face_count = 0
    for face in mesh_desc.faces:
        try:
            b_mesh.faces.new((b_mesh.verts[face[2]], b_mesh.verts[face[1]], b_mesh.verts[face[0]]))
        except ValueError as _:  # noqa: PERF203
            invalid_face_count += 1

    if invalid_face_count > 0:
        logger.info(f"Skipped {invalid_face_count} invalid faces in mesh {file_path.stem}")  # noqa: G004

    uv_layer = b_mesh.loops.layers.uv.verify()
    for face in b_mesh.faces:
        for loop in face.loops:
            uv = mesh_desc.uvs[loop.vert.index]
            loop[uv_layer].uv = (uv[0], 1 - uv[1])

    b_mesh.to_mesh(obj_mesh)
    b_mesh.free()

    obj_mesh.normals_split_custom_set_from_vertices(normals)

    obj.location = armature_object.location
    obj.rotation_euler = armature_object.rotation_euler
    obj.scale = armature_object.scale

    return obj
