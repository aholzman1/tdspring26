# Backlog

Tasks are worked top-to-bottom. Mark each item `[x]` when complete.


## To Do for ./exercises/project2/project2_ex1_fbx_tiktok.py

- [x] CLI: Import a specific pointcloud file from the pointclouds/ folder, or import all pointclouds in the folder.
- [x] For each imported pointcloud, allow rotation in the scene via CLI, name the object 'Pointcloud', and apply the geometry node group bpy.data.node_groups["RadianceField"] from radiancefield.blend.
- [ ] The bounding box for the pointcloud should be set in bpy.data.objects["Pointcloud"].modifiers["GeometryNodes"]["Socket_3"][0], bpy.data.objects["Pointcloud"].modifiers["GeometryNodes"]["Socket_3"][1], bpy.data.objects["Pointcloud"].modifiers["GeometryNodes"]["Socket_3"][2] (this will be available after we apply the geometry node to the pointcloud)
- [ ] After importing pointcloud(s), import either a specific character FBX file or all FBX files from a folder. Place each character at a specified location and rotation (best fit for the pointcloud) via CLI.
- [ ] Render either a single frame (for testing) or the full animation. Output should be either mp4 or png, with filenames combining the pointcloud and character names (e.g., pointcloudname_charactername.mp4 or .png). We should use the tiktok animation renderer technique

