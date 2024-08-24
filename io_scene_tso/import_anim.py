"""Import The Sims Online anim files."""

import bpy
import mathutils
import pathlib

from . import anim
from . import utils


def create_fcurve_data(action: bpy.types.Action, data_path: str, index: int, count: int, data: list[float]) -> None:
    """Create the fcurve data for all frames at once."""
    f_curve = action.fcurves.new(data_path, index=index)
    f_curve.keyframe_points.add(count=count)
    f_curve.keyframe_points.foreach_set("co", data)
    f_curve.update()


MAX_TIMELINE_MARKER_NAME_LENGTH = 63  # 64 - null


def import_anim(
    context: bpy.types.Context,
    file_path: pathlib.Path,
    armature_object: bpy.types.Object,
) -> None:
    """Import an anim file."""
    animation = anim.read_file(file_path)

    if animation.name in bpy.data.actions:
        return

    armature_object.animation_data_create()

    armature_object.animation_data.action = bpy.data.actions.new(name=animation.name)
    action = armature_object.animation_data.action

    action.frame_range = (1.0, animation.motions[0].frame_count)

    action["Distance"] = animation.distance

    for motion in animation.motions:
        bone = armature_object.pose.bones.get(motion.bone_name)
        if bone is None:
            continue

        parent_bone_matrix = mathutils.Matrix()
        if bone.parent:
            parent_bone_matrix = bone.parent.bone.matrix_local @ utils.BONE_ROTATION_OFFSET_INVERTED

        positions_x: list[float] = []
        positions_y: list[float] = []
        positions_z: list[float] = []
        rotations_w: list[float] = []
        rotations_x: list[float] = []
        rotations_y: list[float] = []
        rotations_z: list[float] = []

        for frame in range(motion.frame_count):
            translation = mathutils.Matrix()
            if motion.uses_positions:
                translation = animation.translations[motion.position_offset + frame]
                translation = mathutils.Matrix.Translation(
                    mathutils.Vector(
                        (
                            translation[0] / utils.BONE_SCALE,
                            translation[2] / utils.BONE_SCALE,  # swap y and z
                            translation[1] / utils.BONE_SCALE,
                        ),
                    ),
                )

            rotation = mathutils.Matrix()
            if motion.uses_rotations:
                rotation = animation.rotations[motion.rotation_offset + frame]
                rotation = (
                    mathutils.Quaternion(
                        (
                            rotation[3],
                            rotation[0],
                            rotation[2],  # swap y and z
                            rotation[1],
                        ),
                    )
                    .to_matrix()
                    .to_4x4()
                )

            bone_matrix = parent_bone_matrix @ (translation @ rotation)
            bone_matrix = bone.bone.convert_local_to_pose(
                bone_matrix,
                bone.bone.matrix_local,
                invert=True,
            )
            bone_matrix @= utils.BONE_ROTATION_OFFSET

            if motion.uses_positions:
                translation = bone_matrix.to_translation()
                positions_x += (float(frame + 1), translation.x)
                positions_y += (float(frame + 1), translation.y)
                positions_z += (float(frame + 1), translation.z)

            if motion.uses_rotations:
                rotation = bone_matrix.to_quaternion()
                rotations_w += (float(frame + 1), rotation.w)
                rotations_x += (float(frame + 1), rotation.x)
                rotations_y += (float(frame + 1), rotation.y)
                rotations_z += (float(frame + 1), rotation.z)

        if motion.uses_positions:
            data_path = bone.path_from_id("location")
            create_fcurve_data(action, data_path, 0, motion.frame_count, positions_x)
            create_fcurve_data(action, data_path, 1, motion.frame_count, positions_y)
            create_fcurve_data(action, data_path, 2, motion.frame_count, positions_z)

        if motion.uses_rotations:
            data_path = bone.path_from_id("rotation_quaternion")
            create_fcurve_data(action, data_path, 0, motion.frame_count, rotations_w)
            create_fcurve_data(action, data_path, 1, motion.frame_count, rotations_x)
            create_fcurve_data(action, data_path, 2, motion.frame_count, rotations_y)
            create_fcurve_data(action, data_path, 3, motion.frame_count, rotations_z)

    for motion in animation.motions:
        for time_property_list in motion.time_property_lists:
            for time_property in time_property_list.time_properties:
                for property_list in time_property.property_lists:
                    for event in property_list.properties:
                        event_string = f"{motion.bone_name} {event.name} {event.value}"
                        frame = int(round(time_property.time / 33.333333)) + 1

                        markers = [x for x in action.pose_markers if x.frame == frame]

                        if len(markers) == 0:
                            marker = action.pose_markers.new(name=event_string)
                            marker.frame = frame
                        else:
                            last_marker = action.pose_markers[-1]
                            if len(last_marker.name) + 1 + len(event_string) <= MAX_TIMELINE_MARKER_NAME_LENGTH:
                                last_marker.name = f"{last_marker.name};{event_string}"
                            else:
                                marker = action.pose_markers.new(name=event_string)
                                marker.frame = frame

    track = armature_object.animation_data.nla_tracks.new(prev=None)
    track.name = animation.name
    track.strips.new(animation.name, 1, action)
    track.mute = True

    context.scene.render.fps = 33
    context.scene.frame_end = max(context.scene.frame_end, animation.motions[0].frame_count)
