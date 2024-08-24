"""Export The Sims Online 3D files."""

import bpy
import pathlib

from . import export_anim


def export_files(
    context: bpy.types.Context,
    output_directory: pathlib.Path,
    *,
    export_animations: bool,
) -> None:
    """Export all the meshes and animations in the scene."""
    if export_animations:
        for armature_object in [obj for obj in context.scene.objects if obj.type == 'ARMATURE']:
            if armature_object.animation_data is not None and armature_object.animation_data.nla_tracks is not None:
                for nla_track in armature_object.animation_data.nla_tracks:
                    for strip in nla_track.strips:
                        export_anim.export_anim(output_directory, armature_object, strip.action)
