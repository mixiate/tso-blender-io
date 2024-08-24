"""TSO Blender IO."""

bl_info = {
    "name": "The Sims Online 3D Formats",
    "description": "Import and export The Sims Online meshes and animations.",
    "author": "mix",
    "version": (1, 0, 0),
    "blender": (4, 1, 0),
    "location": "File > Import-Export",
    "warning": "",
    "doc_url": "https://github.com/mixsims/tso-blender-io/wiki",
    "tracker_url": "https://github.com/mixsims/tso-blender-io/issues",
    "support": "COMMUNITY",
    "category": "Import-Export",
}


if "bpy" in locals():
    import sys
    import importlib

    for name in tuple(sys.modules):
        if name.startswith(__name__ + "."):
            importlib.reload(sys.modules[name])


import bpy  # noqa: E402
import bpy_extras  # noqa: E402
import typing  # noqa: E402


class TSOIOImport(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """Import The Sims Online files."""

    bl_idname: str = "tsoblenderio.import"
    bl_label: str = "The Sims Online (.skel/.mesh/.anim)"
    bl_description: str = "Import a skel, mesh or anim file from The Sims Online"
    bl_options: typing.ClassVar[set[str]] = {'UNDO'}

    filter_glob: bpy.props.StringProperty(  # type: ignore[valid-type]
        default="*.skel;*.mesh;*.anim",
        options={'HIDDEN'},
    )
    files: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="File Path",
        type=bpy.types.OperatorFileListElement,
    )
    directory: bpy.props.StringProperty(  # type: ignore[valid-type]
        subtype='DIR_PATH',
    )

    cleanup_meshes: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Cleanup Meshes (Lossy)",
        description="Merge the vertices of the mesh, add sharp edges, remove original normals and shade smooth",
        default=True,
    )

    def execute(self, context: bpy.context) -> set[str]:
        """Execute the importing function."""
        import io
        import logging
        import pathlib
        from . import import_files

        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        log_stream = io.StringIO()
        logger.addHandler(logging.StreamHandler(stream=log_stream))

        directory = pathlib.Path(self.directory)
        paths = [directory / file.name for file in self.files]

        import_files.import_files(
            context,
            logger,
            paths,
            cleanup_meshes=self.cleanup_meshes,
        )

        log_output = log_stream.getvalue()
        if log_output != "":
            self.report({"ERROR"}, log_output)

        return {'FINISHED'}

    def draw(self, _: bpy.context) -> None:
        """Draw the import options ui."""
        col = self.layout.column()
        col.prop(self, "cleanup_meshes")


class TSOIOExport(bpy.types.Operator):
    """Import The Sims Online files."""

    bl_idname = "tsoblenderio.export"
    bl_label = "The Sims Online (.mesh/.anim)"
    bl_description = "Export mesh and anim files for The Sims Online"

    directory: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Output Directory Path",
        description="Output Directory Path",
        subtype='DIR_PATH',
    )

    filter_folder: bpy.props.BoolProperty(  # type: ignore[valid-type]
        default=True, options={"HIDDEN"}
    )

    export_animations: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export Animations",
        default=True,
    )

    def execute(self, context: bpy.context) -> set[str]:
        """Execute the exporting function."""
        import pathlib
        from . import export_files

        export_files.export_files(
            context,
            pathlib.Path(self.properties.directory),
            export_animations=self.export_animations,
        )

        return {'FINISHED'}

    def invoke(self, context: bpy.context, _: bpy.types.Event) -> None:
        """Invoke the file selection window."""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, _: bpy.context) -> None:
        """Draw the export options ui."""
        col = self.layout.column()
        col.prop(self, "export_animations")


def menu_import(self: bpy.types.TOPBAR_MT_file_import, _: bpy.context) -> None:
    """Add an entry to the import menu."""
    self.layout.operator(TSOIOImport.bl_idname)


def menu_export(self: bpy.types.TOPBAR_MT_file_export, _: bpy.context) -> None:
    """Add an entry to the export menu."""
    self.layout.operator(TSOIOExport.bl_idname)


classes = (TSOIOImport, TSOIOExport)


def register() -> None:
    """Register with Blender."""
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_export)


def unregister() -> None:
    """Unregister with Blender."""
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.TOPBAR_MT_file_import.remove(menu_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_export)


if __name__ == "__main__":
    register()
