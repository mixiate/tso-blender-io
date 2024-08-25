TSO Blender IO is an add-on for [Blender](https://www.blender.org/) which allows you to import and export the 3D file formats from The Sims Online.

Blender 4.1.1, 4.2 and 4.2.1 are supported.

### Features
- Import skeletons
- Import and export meshes
- Import and export animations
- Cross compatible with The Sims 1 skeletons, meshes and animations imported with [TS1 Blender IO](https://github.com/mixsims/ts1-blender-io)

### How to use
- To import meshes or animations, first import the skeleton, then select it before importing a mesh or animation file
- Exporting will export all meshes, and all the animations in nla tracks of armatures.
- All vertices of meshes must be skinned to either 1 or 2 bones of the parented armature.
- Animation events are created as pose markers in the format of `<bone> <eventname> <eventvalue>`, with multiple on one frame separated by ;.

### Known issues
- No textures are automatically imported.
- Mesh exporting is not very useful as is because no bnd or apr files are created. It could be possible to manually create these files.
