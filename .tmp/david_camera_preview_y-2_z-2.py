from pathlib import Path
import importlib.util

script_path = Path('/Users/andrewholzman/src/tdspring26/exercises/project2/project2_ex1_fbx_tiktok.py')
spec = importlib.util.spec_from_file_location('project2_ex1_fbx_tiktok', script_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

root = Path('/Users/andrewholzman/src/tdspring26')
pointcloud_path = root / 'pointclouds' / 'David_Bust_point_cloud.ply'
character_path = root / 'characters' / 'doozy-hiphop.fbx'
output_path = root / 'doozy-hiphop_David_Bust_point_cloud_camera_preview_y-2_z-2.blend'

mod.reset_scene()
mod.ensure_object_mode()
node_group = mod.append_radiance_field_node_group(mod.RADIANCE_FIELD_BLEND)
pointcloud_objects = mod.import_ply(pointcloud_path)
pointcloud_obj = next((o for o in pointcloud_objects if o.type == 'MESH'), pointcloud_objects[0])
mod.name_and_rotate_pointcloud(pointcloud_obj, name='Pointcloud', rotation_deg=(90.0, 0.0, 0.0))
mod.apply_radiance_field_to_object(pointcloud_obj, node_group)
mod.set_bounding_box(pointcloud_obj, (4.0, 4.0, 8.0))

character_objects = mod.import_and_place_fbx(
    character_path,
    location=(0.0, -2.0, -2.0),
    rotation_deg=(90.0, 0.0, 0.0),
)
armature = mod.find_armature(character_objects)
if armature:
    camera = mod.create_tiktok_camera()
    mod.setup_camera_tracking(camera, armature, character_objects, mod.TARGET_BONE_NAME, 1, 250)
    mod.add_studio_lighting()

mod.save_blend_file(output_path)
print(f'PREVIEW_BLEND={output_path}')
