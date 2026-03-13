"""Preview blend: McLaren point cloud + Doozy"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import exercises.project2.project2_ex1_fbx_tiktok as mod

pointcloud_path = Path("pointclouds/McLaren_point_cloud.ply")
character_path = Path("characters/doozy-hiphop.fbx")
output_path = Path("mclaren_doozy_preview.blend")

mod.reset_scene()
mod.ensure_object_mode()

node_group = mod.append_radiance_field_node_group(mod.RADIANCE_FIELD_BLEND)
pointcloud_objects = mod.import_ply(pointcloud_path)
pointcloud_obj = next((o for o in pointcloud_objects if o.type == 'MESH'), pointcloud_objects[0])
mod.name_and_rotate_pointcloud(pointcloud_obj, name='Pointcloud', rotation_deg=(90.0, 0.0, 0.0))
mod.apply_radiance_field_to_object(pointcloud_obj, node_group)
mod.set_bounding_box(pointcloud_obj, (4.0, 4.0, 8.0))

character_objects = mod.import_and_place_fbx(character_path, location=(0.0, -2.0, -1.85), rotation_deg=(90.0, 0.0, 0.0))
armature = mod.find_armature(character_objects)
if armature:
    camera = mod.create_tiktok_camera()
    mod.setup_camera_tracking(camera, armature, character_objects, mod.TARGET_BONE_NAME, 1, 250)
    mod.add_studio_lighting()
else:
    print("WARNING: No armature found in character objects")

mod.save_blend_file(output_path)
print(f"Preview saved to {output_path}")
