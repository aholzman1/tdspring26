"""Week 1 Exercise 1: bootstrap a Blender scene and animate a cube via bpy."""

import bpy
from pathlib import Path

FRAME_END = 30
SAVE_NAME = "week1ex1.blend"


def reset_scene() -> None:
    """Return to a predictable factory scene and clear leftover data."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = FRAME_END
    bpy.context.view_layer.update()


def ensure_object_mode() -> None:
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")


def clear_objects() -> None:
    ensure_object_mode()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def create_ground() -> bpy.types.Object:
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0.0, 0.0, -1.0))
    plane = bpy.context.active_object
    material = bpy.data.materials.new(name="GroundMaterial")  # type: ignore
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs[0].default_value = (0.1, 0.1, 0.12, 1.0)
    plane.data.materials.append(material)
    return plane


def create_cube() -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(
        size=2.0, enter_editmode=False, location=(0.0, 0.0, 0.0)
    )
    cube = bpy.context.active_object
    cube.name = "Week1Cube"
    cube.data.materials.clear()
    material = bpy.data.materials.new(name="CubeMaterial")  # type: ignore
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs[0].default_value = (0.8, 0.2, 0.15, 1.0)
    cube.data.materials.append(material)
    return cube


def keyframe_cube(cube: bpy.types.Object) -> None:
    cube.animation_data_clear()
    timeline = (
        (1, (0.0, 0.0, 0.0)),
        (15, (0.0, -10.0, 0.0)),
        (30, (30.0, 0.0, 0.0)),
    )
    for frame, location in timeline:
        cube.location = location
        cube.keyframe_insert(data_path="location", frame=frame)


def main() -> None:
    reset_scene()
    clear_objects()
    create_ground()
    cube = create_cube()
    keyframe_cube(cube)
    output_path = Path(__file__).with_name(SAVE_NAME)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    print(f"Week 1 Exercise 1 saved to {output_path}")


if __name__ == "__main__":
    main()
