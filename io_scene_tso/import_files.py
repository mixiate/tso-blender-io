"""Import The Sims Online 3D files."""

import bpy
import logging
import pathlib

from . import import_skel
from . import utils


def import_files(
    context: bpy.types.Context,
    logger: logging.Logger,
    file_paths: list[pathlib.Path],
) -> None:
    """Import all the selected files."""
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    if bpy.ops.object.select_all.poll():
        bpy.ops.object.select_all(action='DESELECT')

    for file_path in file_paths:
        try:
            if file_path.suffix == ".skel":
                import_skel.import_skel(context, file_path)

        except utils.FileReadError as _:  # noqa: PERF203
            logger.info(f"Could not import {file_path}")  # noqa: G004
