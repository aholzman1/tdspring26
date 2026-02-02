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
FRAME_STEP = 5  # Bake keyframes every N frames
CAMERA_DISTANCE = 2.5  # Distance from target in meters
CAMERA_HEIGHT_OFFSET = 1.5  # Height above target center
TARGET_BONE_NAME = "mixamorig:Hips"  # Common Mixamo bone name


def reset_scene() -> None:
    """Reset to a clean scene with proper settings."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
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

    # Import FBX
    bpy.ops.import_scene.fbx(filepath=str(fbx_path))

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
        import math

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


if __name__ == "__main__":
    app()
