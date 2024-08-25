"""Export The Sims Online 3D files."""

import bpy
import logging
import pathlib

from . import export_anim
from . import export_mesh


def export_files(
    context: bpy.types.Context,
    logger: logging.Logger,
    output_directory: pathlib.Path,
    *,
    export_meshes: bool,
    export_animations: bool,
) -> None:
    """Export all the meshes and animations in the scene."""
    if export_meshes:
        for mesh_object in [obj for obj in context.scene.objects if obj.type == 'MESH']:
            export_mesh.export_mesh(logger, output_directory, mesh_object)

    if export_animations:
        for armature_object in [obj for obj in context.scene.objects if obj.type == 'ARMATURE']:
            if armature_object.animation_data is not None and armature_object.animation_data.nla_tracks is not None:
                for nla_track in armature_object.animation_data.nla_tracks:
                    for strip in nla_track.strips:
                        export_anim.export_anim(output_directory, armature_object, strip.action)
