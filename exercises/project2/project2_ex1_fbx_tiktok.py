"""Week 2 Exercise 4: FBX Import with TikTok-Style Camera Follow

This script uses typer to create a CLI tool that:
1. Imports an FBX file containing an animated character
2. Creates a vertical (9:16) TikTok-style camera setup
3. Automatically follows the character's animation with smooth tracking
"""

from pathlib import Path
from typing import Optional

import bpy
import typer
from mathutils import Vector
from typing_extensions import Annotated

app = typer.Typer(help="Import FBX and create TikTok-style camera automation")

SAVE_NAME = "week2ex4_tiktok.blend"
RADIANCE_FIELD_BLEND = Path(__file__).parent / "radiancefield.blend"
RADIANCE_FIELD_NODE_GROUP = "RadianceField"
FRAME_STEP = 5  # Bake keyframes every N frames
CAMERA_DISTANCE = 2.5  # Distance from target in meters
CAMERA_HEIGHT_OFFSET = 1.5  # Height above target center
TARGET_BONE_NAME = "mixamorig:Hips"  # Common Mixamo bone name


import math


def import_ply(ply_path: Path) -> list[bpy.types.Object]:
    """Import a PLY pointcloud file and return the imported objects."""
    if not ply_path.exists():
        typer.secho(f"Error: PLY file not found: {ply_path}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.echo(f"Importing PLY: {ply_path}")
    objects_before = set(bpy.data.objects)
    bpy.ops.wm.ply_import(filepath=str(ply_path))
    objects_after = set(bpy.data.objects)
    imported = list(objects_after - objects_before)
    typer.secho(f"✓ Imported {len(imported)} object(s) from {ply_path.name}", fg=typer.colors.GREEN)
    return imported


def name_and_rotate_pointcloud(
    obj: bpy.types.Object,
    name: str = "Pointcloud",
    rotation_deg: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> None:
    """Rename the object and apply rotation (in degrees, converted to radians)."""
    obj.name = name
    obj.rotation_euler = (
        math.radians(rotation_deg[0]),
        math.radians(rotation_deg[1]),
        math.radians(rotation_deg[2]),
    )
    typer.secho(
        f"✓ Named '{name}', rotation={rotation_deg[0]}°, {rotation_deg[1]}°, {rotation_deg[2]}°",
        fg=typer.colors.GREEN,
    )


def append_radiance_field_node_group(blend_path: Path) -> bpy.types.NodeTree:
    """Append the RadianceField node group from a .blend file."""
    if not blend_path.exists():
        typer.secho(f"Error: radiancefield.blend not found: {blend_path}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # Check if already appended
    if RADIANCE_FIELD_NODE_GROUP in bpy.data.node_groups:
        typer.echo(f"Node group '{RADIANCE_FIELD_NODE_GROUP}' already loaded.")
        return bpy.data.node_groups[RADIANCE_FIELD_NODE_GROUP]

    typer.echo(f"Appending node group '{RADIANCE_FIELD_NODE_GROUP}' from {blend_path.name}")
    bpy.ops.wm.append(
        filepath=str(blend_path) + f"/NodeTree/{RADIANCE_FIELD_NODE_GROUP}",
        directory=str(blend_path) + "/NodeTree/",
        filename=RADIANCE_FIELD_NODE_GROUP,
    )

    if RADIANCE_FIELD_NODE_GROUP not in bpy.data.node_groups:
        typer.secho(
            f"Error: Could not find node group '{RADIANCE_FIELD_NODE_GROUP}' after append.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    typer.secho(f"✓ Appended node group '{RADIANCE_FIELD_NODE_GROUP}'", fg=typer.colors.GREEN)
    return bpy.data.node_groups[RADIANCE_FIELD_NODE_GROUP]


def apply_radiance_field_to_object(
    obj: bpy.types.Object, node_group: bpy.types.NodeTree
) -> None:
    """Add a GeometryNodes modifier to obj and assign the RadianceField node group."""
    mod = obj.modifiers.new(name="GeometryNodes", type="NODES")
    mod.node_group = node_group
    typer.secho(
        f"✓ Applied '{RADIANCE_FIELD_NODE_GROUP}' geometry nodes to '{obj.name}'",
        fg=typer.colors.GREEN,
    )


def set_bounding_box(
    obj: bpy.types.Object,
    bbox: tuple[float, float, float] = (4.0, 4.0, 8.0),
) -> None:
    """Set Socket_3 (bounding box vector) on the GeometryNodes modifier."""
    mod = obj.modifiers.get("GeometryNodes")
    if mod is None:
        typer.secho(f"Warning: No GeometryNodes modifier on '{obj.name}'", fg=typer.colors.YELLOW)
        return
    mod["Socket_3"] = bbox
    typer.secho(
        f"✓ Bounding box set to {bbox} on '{obj.name}'",
        fg=typer.colors.GREEN,
    )


def reset_scene() -> None:
    bpy.context.scene.render.engine = "BLENDER_EEVEE"

    # TikTok aspect ratio: 9:16 (vertical video)
    bpy.context.scene.render.resolution_x = 1080
    bpy.context.scene.render.resolution_y = 1920
    bpy.context.scene.render.resolution_percentage = 100


def ensure_object_mode() -> None:
    """Ensure we're in object mode."""
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")


def import_fbx(fbx_path: Path) -> list[bpy.types.Object]:
    """Import FBX file and return imported objects."""
    if not fbx_path.exists():
        typer.secho(f"Error: FBX file not found: {fbx_path}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.echo(f"Importing FBX: {fbx_path}")

    # Get objects before import
    objects_before = set(bpy.data.objects)

    # Import FBX (bpy 5.x: operator moved to bpy.ops.wm.fbx_import)
    bpy.ops.wm.fbx_import(filepath=str(fbx_path))

    # Get newly imported objects
    objects_after = set(bpy.data.objects)
    imported_objects = list(objects_after - objects_before)

    typer.secho(f"✓ Imported {len(imported_objects)} objects", fg=typer.colors.GREEN)
    return imported_objects


def find_armature(
    imported_objects: list[bpy.types.Object],
) -> Optional[bpy.types.Object]:
    """Find the armature object from imported objects."""
    for obj in imported_objects:
        if obj.type == "ARMATURE":
            return obj
    return None


def get_target_world_location(
    armature: bpy.types.Object, bone_name: str
) -> tuple[float, float, float]:
    """Get world location of a bone in the armature."""
    if bone_name in armature.pose.bones:
        bone = armature.pose.bones[bone_name]
        matrix = armature.matrix_world @ bone.matrix
        return tuple(matrix.translation)

    # Fallback to armature origin
    return tuple(armature.matrix_world.translation)


def create_tiktok_camera(name: str = "TikTokCamera") -> bpy.types.Object:
    """Create a camera optimized for TikTok-style vertical video."""
    bpy.ops.object.camera_add()
    camera = bpy.context.active_object
    camera.name = name
    camera.data.name = f"{name}_data"

    # Camera settings for portrait video
    camera.data.lens = 50  # Standard focal length
    camera.data.sensor_width = 36
    camera.data.sensor_height = 36 * (16 / 9)  # Adjust sensor for vertical

    # Set as active camera
    bpy.context.scene.camera = camera

    return camera


def setup_camera_tracking(
    camera: bpy.types.Object,
    target: bpy.types.Object,
    bone_name: Optional[str] = None,
    frame_start: int = 1,
    frame_end: int = 250,
) -> None:
    """Setup camera to follow the target with baked keyframes."""
    typer.echo(f"Setting up camera tracking from frame {frame_start} to {frame_end}")

    # Clear existing animation data
    if camera.animation_data:
        camera.animation_data_clear()

    scene = bpy.context.scene

    # Bake keyframes
    for frame in range(frame_start, frame_end + 1, FRAME_STEP):
        scene.frame_set(frame)

        # Get target location
        if target.type == "ARMATURE" and bone_name:
            target_loc = get_target_world_location(target, bone_name)
        else:
            target_loc = tuple(target.matrix_world.translation)

        # Position camera behind and above target
        camera.location = (
            target_loc[0],
            target_loc[1] - CAMERA_DISTANCE,
            target_loc[2] + CAMERA_HEIGHT_OFFSET,
        )

        # Point camera at target
        direction = Vector(
            (
                target_loc[0] - camera.location[0],
                target_loc[1] - camera.location[1],
                target_loc[2] - camera.location[2],
            )
        )

        # Calculate rotation to look at target
        rot_quat = camera.rotation_euler.to_quaternion()
        track_quat = direction.to_track_quat("-Z", "Y")
        camera.rotation_euler = track_quat.to_euler()

        # Insert keyframes
        camera.keyframe_insert(data_path="location", frame=frame)
        camera.keyframe_insert(data_path="rotation_euler", frame=frame)

    typer.secho(
        f"✓ Baked {(frame_end - frame_start) // FRAME_STEP + 1} keyframes",
        fg=typer.colors.GREEN,
    )


def add_studio_lighting() -> None:
    """Add basic three-point lighting setup."""
    typer.echo("Adding studio lighting")

    # Key light
    bpy.ops.object.light_add(type="AREA", location=(2, -2, 4))
    key_light = bpy.context.active_object
    key_light.name = "KeyLight"
    key_light.data.energy = 200
    key_light.data.size = 2

    # Fill light
    bpy.ops.object.light_add(type="AREA", location=(-2, -1, 2))
    fill_light = bpy.context.active_object
    fill_light.name = "FillLight"
    fill_light.data.energy = 100
    fill_light.data.size = 2

    # Rim light
    bpy.ops.object.light_add(type="SPOT", location=(0, 2, 3))
    rim_light = bpy.context.active_object
    rim_light.name = "RimLight"
    rim_light.data.energy = 150

    typer.secho("✓ Lighting setup complete", fg=typer.colors.GREEN)


def save_blend_file(output_path: Optional[Path] = None) -> None:
    """Save the blend file."""
    if output_path is None:
        output_path = Path.cwd() / SAVE_NAME

    output_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    typer.secho(f"✓ Saved: {output_path}", fg=typer.colors.GREEN)


@app.command()
def create(
    fbx_file: Annotated[Path, typer.Argument(help="Path to the FBX file to import")],
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Output .blend file path"),
    ] = None,
    bone: Annotated[
        str,
        typer.Option("--bone", "-b", help="Target bone name for camera tracking"),
    ] = TARGET_BONE_NAME,
    start_frame: Annotated[
        int, typer.Option("--start", "-s", help="Animation start frame")
    ] = 1,
    end_frame: Annotated[
        int, typer.Option("--end", "-e", help="Animation end frame")
    ] = 250,
    no_lights: Annotated[
        bool, typer.Option("--no-lights", help="Skip adding studio lights")
    ] = False,
) -> None:
    """Import an FBX file and create a TikTok-style camera that follows the animation.

    Example:
        blender --background --python week2_ex4_fbx_tiktok.py -- create character.fbx
        blender --background --python week2_ex4_fbx_tiktok.py -- create character.fbx --output my_scene.blend
    """
    typer.secho("🎬 TikTok Camera Setup", fg=typer.colors.CYAN, bold=True)
    typer.echo("=" * 50)

    # Step 1: Reset scene
    typer.echo("1. Resetting scene...")
    reset_scene()
    ensure_object_mode()

    # Step 2: Import FBX
    typer.echo(f"2. Importing FBX: {fbx_file}")
    imported_objects = import_fbx(fbx_file)

    # Step 3: Find armature
    typer.echo("3. Looking for armature...")
    armature = find_armature(imported_objects)

    if not armature:
        typer.secho(
            "Warning: No armature found. Using first imported object as target.",
            fg=typer.colors.YELLOW,
        )
        target = imported_objects[0] if imported_objects else None
        if not target:
            typer.secho("Error: No objects imported!", fg=typer.colors.RED)
            raise typer.Exit(code=1)
        target_bone = None
    else:
        typer.secho(f"✓ Found armature: {armature.name}", fg=typer.colors.GREEN)
        target = armature
        target_bone = bone

    # Step 4: Set frame range
    bpy.context.scene.frame_start = start_frame
    bpy.context.scene.frame_end = end_frame

    # Step 5: Create camera
    typer.echo("4. Creating TikTok-style camera...")
    camera = create_tiktok_camera()

    # Step 6: Setup tracking
    typer.echo("5. Setting up camera tracking...")
    setup_camera_tracking(camera, target, target_bone, start_frame, end_frame)

    # Step 7: Add lighting
    if not no_lights:
        typer.echo("6. Adding studio lighting...")
        add_studio_lighting()
    else:
        typer.echo("6. Skipping lights (--no-lights specified)")

    # Step 8: Save file
    typer.echo("7. Saving blend file...")
    save_blend_file(output)

    typer.echo("=" * 50)
    typer.secho("✨ Setup complete!", fg=typer.colors.GREEN, bold=True)
    typer.echo(f"Camera: {camera.name}")
    typer.echo(f"Target: {target.name}")
    if target_bone:
        typer.echo(f"Tracking bone: {target_bone}")
    typer.echo(f"Frame range: {start_frame} - {end_frame}")


@app.command("import-pointcloud")
def import_pointcloud_cmd(
    pointcloud: Annotated[
        Optional[Path],
        typer.Option("--pointcloud", "-p", help="Path to a single .ply pointcloud file"),
    ] = None,
    pointcloud_dir: Annotated[
        Optional[Path],
        typer.Option("--pointcloud-dir", "-d", help="Directory of .ply files to import all"),
    ] = None,
    rotation: Annotated[
        Optional[list[float]],
        typer.Option("--rotation", "-r", help="Rotation in degrees: X Y Z (pass three times)"),
    ] = None,
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Output .blend file path"),
    ] = None,
    radiance_field_blend: Annotated[
        Path,
        typer.Option("--radiance-field", help="Path to radiancefield.blend"),
    ] = RADIANCE_FIELD_BLEND,
    bounding_box: Annotated[
        Optional[list[float]],
        typer.Option("--bounding-box", "-b", help="Bounding box X Y Z (pass three times, default 4 4 8)"),
    ] = None,
) -> None:
    """Import one or all .ply pointclouds, apply rotation, name them 'Pointcloud',
    and attach the RadianceField geometry node group.

    Examples:
        python script.py import-pointcloud --pointcloud pointclouds/Hydrant.ply --rotation 0 --rotation 0 --rotation 45
        python script.py import-pointcloud --pointcloud-dir pointclouds/
    """
    typer.secho("☁️  Pointcloud Import", fg=typer.colors.CYAN, bold=True)
    typer.echo("=" * 50)

    if pointcloud is None and pointcloud_dir is None:
        typer.secho("Error: Provide --pointcloud or --pointcloud-dir.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # Collect files to import
    if pointcloud is not None:
        ply_files = [pointcloud]
    else:
        pointcloud_dir = pointcloud_dir.expanduser().resolve()
        ply_files = sorted(pointcloud_dir.glob("*.ply"))
        if not ply_files:
            typer.secho(f"Error: No .ply files found in {pointcloud_dir}", fg=typer.colors.RED)
            raise typer.Exit(code=1)
        typer.echo(f"Found {len(ply_files)} .ply file(s) in {pointcloud_dir}")

    # Parse rotation (defaults to 0, 0, 0). +90° X base offset corrects PLY Z-forward → Z-up.
    rot: tuple[float, float, float]
    if rotation is not None:
        if len(rotation) != 3:
            typer.secho("Error: --rotation requires exactly 3 values (X Y Z).", fg=typer.colors.RED)
            raise typer.Exit(code=1)
        rot = (rotation[0] + 90.0, rotation[1], rotation[2])
    else:
        rot = (90.0, 0.0, 0.0)

    typer.echo("1. Resetting scene...")
    reset_scene()
    ensure_object_mode()

    typer.echo(f"2. Appending RadianceField node group from {radiance_field_blend.name}...")
    node_group = append_radiance_field_node_group(radiance_field_blend)

    for i, ply_file in enumerate(ply_files):
        typer.echo(f"3. Importing pointcloud {i + 1}/{len(ply_files)}: {ply_file.name}")
        imported = import_ply(ply_file)
        if not imported:
            typer.secho(f"Warning: No objects imported from {ply_file.name}", fg=typer.colors.YELLOW)
            continue

        # Use the first (and typically only) imported mesh object
        obj = next((o for o in imported if o.type == "MESH"), imported[0])

        typer.echo(f"4. Naming and rotating '{obj.name}'...")
        obj_name = "Pointcloud" if len(ply_files) == 1 else f"Pointcloud_{ply_file.stem}"
        name_and_rotate_pointcloud(obj, name=obj_name, rotation_deg=rot)

        typer.echo("5. Applying RadianceField geometry nodes...")
        apply_radiance_field_to_object(obj, node_group)

        typer.echo("6. Setting bounding box...")
        if bounding_box is not None:
            if len(bounding_box) != 3:
                typer.secho("Error: --bounding-box requires exactly 3 values (X Y Z).", fg=typer.colors.RED)
                raise typer.Exit(code=1)
            bbox = (bounding_box[0], bounding_box[1], bounding_box[2])
        else:
            bbox = (4.0, 4.0, 8.0)
        set_bounding_box(obj, bbox)

    typer.echo("7. Saving blend file...")
    save_blend_file(output)

    typer.echo("=" * 50)
    typer.secho("✨ Pointcloud import complete!", fg=typer.colors.GREEN, bold=True)
    typer.echo(f"Imported {len(ply_files)} pointcloud(s) with rotation {rot}")
    typer.echo(f"Bounding box: {bbox}")
    typer.echo("Open the .blend in Blender to verify the GeometryNodes modifier.")


if __name__ == "__main__":
    app()
