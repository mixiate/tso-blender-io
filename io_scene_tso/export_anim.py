"""Export The Sims Online anim files."""

import bpy
import mathutils
import pathlib

from . import anim
from . import utils


def export_anim(
    output_directory: pathlib.Path,
    armature_object: bpy.types.Object,
    action: bpy.types.Action,
) -> None:
    """Export an anim file."""
    translations = []
    rotations = []
    motions = []

    position_offset = 0
    rotation_offset = 0

    for bone in armature_object.pose.bones:
        location_data_path = bone.path_from_id("location")
        rotation_data_path = bone.path_from_id("rotation_quaternion")

        uses_positions = False
        uses_rotations = False

        if action.fcurves.find(location_data_path):
            uses_positions = True
        if action.fcurves.find(rotation_data_path):
            uses_rotations = True

        if not uses_positions and not uses_rotations:
            continue

        parent_bone_matrix = mathutils.Matrix()
        if bone.parent:
            parent_bone_matrix = bone.parent.bone.matrix_local @ utils.BONE_ROTATION_OFFSET_INVERTED

        for frame in range(int(action.frame_start), int(action.frame_end) + 1):
            translation = mathutils.Matrix()
            if uses_positions:
                translation = mathutils.Matrix.Translation(
                    mathutils.Vector(
                        (
                            action.fcurves.find(location_data_path, index=0).evaluate(frame),
                            action.fcurves.find(location_data_path, index=1).evaluate(frame),
                            action.fcurves.find(location_data_path, index=2).evaluate(frame),
                        ),
                    ),
                )

            rotation = mathutils.Matrix()
            if uses_rotations:
                rotation = (
                    mathutils.Quaternion(
                        (
                            action.fcurves.find(rotation_data_path, index=0).evaluate(frame),
                            action.fcurves.find(rotation_data_path, index=1).evaluate(frame),
                            action.fcurves.find(rotation_data_path, index=2).evaluate(frame),
                            action.fcurves.find(rotation_data_path, index=3).evaluate(frame),
                        ),
                    )
                    .to_matrix()
                    .to_4x4()
                )

            bone_matrix = bone.bone.convert_local_to_pose(
                translation @ rotation,
                bone.bone.matrix_local,
            )
            bone_matrix = parent_bone_matrix.inverted() @ bone_matrix
            bone_matrix @= utils.BONE_ROTATION_OFFSET_INVERTED

            if uses_positions:
                translation = bone_matrix.to_translation() * utils.BONE_SCALE
                translations.append(translation)
            if uses_rotations:
                rotation = bone_matrix.to_quaternion()
                rotations.append(rotation)

        time_property_list = anim.TimePropertyList([])

        for frame in range(int(action.frame_start), int(action.frame_end) + 1):
            markers = [x for x in action.pose_markers if x.frame == frame]
            if len(markers) == 0:
                continue

            time = int(round((frame - int(action.frame_start)) * 33.33333))
            events = []

            for marker in markers:
                event_strings = marker.name.split(";")
                for event_string in event_strings:
                    event_components = event_string.split()
                    if event_components[0] != bone.name:
                        continue
                    events.append(
                        utils.Property(
                            event_components[1],
                            event_components[2],
                        ),
                    )

            if len(events) == 0:
                continue

            time_property = anim.TimeProperty(
                time,
                [utils.PropertyList(events)],
            )
            time_property_list.time_properties.append(time_property)

        time_property_lists = []
        if len(time_property_list.time_properties):
            time_property_lists.append(time_property_list)

        motion = anim.Motion(
            bone.name,
            int(action.frame_end - action.frame_start) + 1,
            round((action.frame_end) * 33.3333333),
            uses_positions,
            uses_rotations,
            position_offset if uses_positions else -1,
            rotation_offset if uses_rotations else -1,
            [],
            time_property_lists,
        )

        motions.append(motion)

        if uses_positions:
            position_offset += motion.frame_count
        if uses_rotations:
            rotation_offset += motion.frame_count

    distance = action.get("Distance", 0.0)

    animation = anim.Anim(
        action.name,
        motions[0].duration,
        distance,
        distance != 0.0,
        translations,
        rotations,
        motions,
    )

    anim.write_file(output_directory / (action.name + ".anim"), animation)
