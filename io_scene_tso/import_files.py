"""Import The Sims Online 3D files."""

import bpy
import logging
import pathlib

from . import import_anim
from . import import_mesh
from . import import_skel
from . import utils


def import_files(
    context: bpy.types.Context,
    logger: logging.Logger,
    file_paths: list[pathlib.Path],
    *,
    cleanup_meshes: bool,
) -> None:
    """Import all the selected files."""
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    if bpy.ops.object.select_all.poll():
        bpy.ops.object.select_all(action='DESELECT')

    for file_path in file_paths:
        try:
            if file_path.suffix == ".skel":
                context.view_layer.objects.active = import_skel.import_skel(context, file_path)

        except utils.FileReadError as _:  # noqa: PERF203
            logger.info(f"Could not import {file_path}")  # noqa: G004

    active_armature = context.view_layer.objects.active

    mesh_objects = []

    for file_path in file_paths:
        if active_armature is not None and active_armature.type == 'ARMATURE':
            try:
                if file_path.suffix == ".mesh":
                    mesh_objects.append(import_mesh.import_mesh(context, logger, file_path, active_armature))

                if file_path.suffix == ".anim":
                    import_anim.import_anim(context, file_path, active_armature)

            except utils.FileReadError as _:
                logger.info(f"Could not import {file_path}")  # noqa: G004

        else:
            logger.info("Please select an armature to apply the mesh or animation to.")
            break

    mesh_objects = [obj for obj in mesh_objects if obj is not None]

    if active_armature is not None and active_armature.type == 'ARMATURE' and mesh_objects:
        previous_active_object = context.view_layer.objects.active

        bpy.ops.object.select_all(action='DESELECT')

        for mesh_object in mesh_objects:
            mesh_object.select_set(state=True)

        if cleanup_meshes:
            context.view_layer.objects.active = mesh_objects[0]
            bpy.ops.object.mode_set(mode='EDIT')

            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            bpy.ops.mesh.select_all(action='SELECT')

            bpy.ops.mesh.merge_normals()
            bpy.ops.mesh.remove_doubles(use_sharp_edge_from_normals=True)
            bpy.ops.mesh.faces_shade_smooth()
            bpy.ops.mesh.normals_make_consistent()

            bpy.ops.mesh.select_all(action='DESELECT')

            bpy.ops.object.mode_set(mode='OBJECT')

            for obj in mesh_objects:
                context.view_layer.objects.active = obj
                bpy.ops.mesh.customdata_custom_splitnormals_clear()

        active_armature.select_set(state=True)
        context.view_layer.objects.active = active_armature
        bpy.ops.object.parent_set(type='ARMATURE')

        bpy.ops.object.select_all(action='DESELECT')

        context.view_layer.objects.active = previous_active_object
