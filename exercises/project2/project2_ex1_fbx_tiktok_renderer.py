"""Week 2 Exercise 4: FBX Import with TikTok-Style Camera Follow

This script uses typer to create a CLI tool that:
1. Imports an FBX file containing an animated character
2. Creates a vertical (9:16) TikTok-style camera setup
3. Automatically follows the character's animation with smooth tracking
"""

from pathlib import Path
from typing import Optional
import tempfile
import shutil
import subprocess
import sys

import bpy
import typer
from mathutils import Vector

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


def load_blend_file(blend_path: Path) -> None:
    """Load an existing blend file as a template."""
    if not blend_path.exists():
        typer.secho(f"Error: Blend file not found: {blend_path}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    
    typer.echo(f"Loading blend file: {blend_path}")
    bpy.ops.wm.open_mainfile(filepath=str(blend_path))
    ensure_object_mode()
    typer.secho(f"✓ Loaded blend file", fg=typer.colors.GREEN)


def remove_imported_objects(imported_objects: list[bpy.types.Object]) -> None:
    """Remove imported objects from the scene (for cleanup between batches)."""
    ensure_object_mode()
    for obj in imported_objects:
        if obj.name in bpy.data.objects:
            bpy.data.objects.remove(obj, do_unlink=True)


def import_pointcloud(
    ply_path: Path,
    rotation_xyz: tuple[float, float, float] = (0.0, 0.0, 0.0),
    name: str = "Pointcloud",
) -> bpy.types.Object:
    """Import a PLY pointcloud, name it, and apply rotation.

    Args:
        ply_path: Path to the .ply file.
        rotation_xyz: Rotation in degrees for X, Y, Z axes.
        name: Name to assign the imported object (Blender will auto-increment
              to 'Pointcloud.001' etc. when multiple clouds exist in the scene).

    Returns:
        The imported pointcloud object.
    """
    import math

    if not ply_path.exists():
        typer.secho(f"Error: PLY file not found: {ply_path}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.echo(f"  Importing: {ply_path.name}")
    objects_before = set(bpy.data.objects)

    bpy.ops.wm.ply_import(filepath=str(ply_path))

    objects_after = set(bpy.data.objects)
    new_objects = list(objects_after - objects_before)

    if not new_objects:
        typer.secho(
            f"Error: No objects imported from {ply_path.name}", fg=typer.colors.RED
        )
        raise typer.Exit(code=1)

    pointcloud_obj = new_objects[0]
    pointcloud_obj.name = name

    # Apply rotation (degrees → radians)
    pointcloud_obj.rotation_euler = (
        math.radians(rotation_xyz[0]),
        math.radians(rotation_xyz[1]),
        math.radians(rotation_xyz[2]),
    )

    typer.secho(
        f"  ✓ {pointcloud_obj.name}  rotation=({rotation_xyz[0]:.1f}°, "
        f"{rotation_xyz[1]:.1f}°, {rotation_xyz[2]:.1f}°)",
        fg=typer.colors.GREEN,
    )
    return pointcloud_obj


def render_to_mp4(
    output_path: Path,
    fps: int = 24,
    quality: str = "high",
    frame_start: Optional[int] = None,
    frame_end: Optional[int] = None,
) -> Path:
    """Render animation directly to MP4 file using Blender's FFmpeg.
    
    Args:
        output_path: Path to save the MP4 file
        fps: Frames per second for the output video
        quality: Quality preset - 'high', 'medium', or 'low'
        frame_start: Start frame (defaults to scene start)
        frame_end: End frame (defaults to scene end)
    
    Returns:
        Path to the rendered MP4 file
    """
    scene = bpy.context.scene
    
    # Use scene frame range if not specified
    if frame_start is None:
        frame_start = scene.frame_start
    if frame_end is None:
        frame_end = scene.frame_end
    
    # Quality settings mapping (bitrate in kbps)
    quality_settings = {
        "high": {"bitrate": 8000, "gop": 12},
        "medium": {"bitrate": 4000, "gop": 15},
        "low": {"bitrate": 2000, "gop": 18},
    }
    
    if quality not in quality_settings:
        typer.secho(f"Warning: Unknown quality '{quality}', using 'medium'", fg=typer.colors.YELLOW)
        quality = "medium"
    
    settings = quality_settings[quality]
    
    typer.echo(f"Rendering frames {frame_start} to {frame_end}...")
    
    # Store original settings to restore later
    original_media_type = scene.render.image_settings.media_type
    original_format = scene.render.image_settings.file_format
    original_filepath = scene.render.filepath
    original_start = scene.frame_start
    original_end = scene.frame_end
    
    try:
        # Configure FFmpeg output - IMPORTANT: Set media_type first!
        scene.render.image_settings.media_type = 'VIDEO'
        scene.render.image_settings.file_format = 'FFMPEG'
        scene.render.ffmpeg.format = 'MPEG4'
        scene.render.ffmpeg.codec = 'H264'
        
        # Quality settings
        scene.render.ffmpeg.constant_rate_factor = 'HIGH' if quality == 'high' else 'MEDIUM' if quality == 'medium' else 'LOW'
        scene.render.ffmpeg.ffmpeg_preset = 'GOOD'
        scene.render.ffmpeg.video_bitrate = settings["bitrate"]
        scene.render.ffmpeg.gopsize = settings["gop"]
        
        # Audio settings (disable if not needed)
        scene.render.ffmpeg.audio_codec = 'AAC'
        scene.render.ffmpeg.audio_bitrate = 192
        
        # Frame rate
        scene.render.fps = fps
        scene.render.fps_base = 1.0
        
        # Set output path and frame range
        output_path = output_path.resolve()  # Ensure absolute path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        scene.render.filepath = str(output_path)
        scene.frame_start = frame_start
        scene.frame_end = frame_end
        
        typer.echo(f"Output will be written to: {scene.render.filepath}")
        
        # Render animation
        typer.echo(f"Encoding to MP4 with quality={quality} (bitrate={settings['bitrate']}kbps)...")
        
        with typer.progressbar(
            length=frame_end - frame_start + 1,
            label="Rendering frames"
        ) as progress:
            bpy.ops.render.render(animation=True, write_still=False)
            progress.update(frame_end - frame_start + 1)
        
        typer.secho(f"✓ MP4 rendered successfully: {output_path}", fg=typer.colors.GREEN)
        
        # Get file size
        if output_path.exists():
            file_size_mb = output_path.stat().st_size / (1024 * 1024)
            typer.echo(f"  File size: {file_size_mb:.2f} MB")
            typer.echo(f"  Resolution: {scene.render.resolution_x}x{scene.render.resolution_y}")
            typer.echo(f"  Frame rate: {fps} fps")
            typer.echo(f"  Duration: {(frame_end - frame_start + 1) / fps:.2f} seconds")
        else:
            typer.secho(f"Warning: Output file not found at {output_path}", fg=typer.colors.YELLOW)
        
    except Exception as e:
        typer.secho(f"Error during rendering: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    finally:
        # Restore original settings - restore media_type first!
        scene.render.image_settings.media_type = original_media_type
        scene.render.image_settings.file_format = original_format
        scene.render.filepath = original_filepath
        scene.frame_start = original_start
        scene.frame_end = original_end
    
    return output_path


@app.command()
def import_pointclouds(
    pointcloud: Path = typer.Argument(
        ...,
        help="Path to a single .ply file OR a folder containing .ply files",
    ),
    rotation_x: float = typer.Option(0.0, "--rx", help="Rotation around X axis in degrees"),
    rotation_y: float = typer.Option(0.0, "--ry", help="Rotation around Y axis in degrees"),
    rotation_z: float = typer.Option(0.0, "--rz", help="Rotation around Z axis in degrees"),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output .blend file path (defaults to pointcloud stem + .blend)"
    ),
) -> None:
    """Import one or all pointcloud PLY files and save a .blend file.

    Provide a single .ply file to import just that cloud, or a folder path
    to import every .ply file inside it. Each object is named 'Pointcloud'
    (Blender auto-increments to 'Pointcloud.001', 'Pointcloud.002', … for
    multiple clouds in the same scene).

    Examples:
        blender --background --python project2_ex1_fbx_tiktok_renderer.py -- \\
            import-pointclouds pointclouds/McLaren_point_cloud.ply

        blender --background --python project2_ex1_fbx_tiktok_renderer.py -- \\
            import-pointclouds pointclouds/ --rx 90 --output my_clouds.blend
    """
    typer.secho("☁  Importing Pointcloud(s)", fg=typer.colors.CYAN, bold=True)
    typer.echo("=" * 50)

    # Gather PLY files to import
    if pointcloud.is_dir():
        ply_files = sorted(pointcloud.glob("*.ply"))
        if not ply_files:
            typer.secho(
                f"Error: No .ply files found in {pointcloud}", fg=typer.colors.RED
            )
            raise typer.Exit(code=1)
        typer.echo(f"Found {len(ply_files)} .ply file(s) in {pointcloud}")
    elif pointcloud.suffix.lower() == ".ply":
        ply_files = [pointcloud]
    else:
        typer.secho(
            f"Error: Expected a .ply file or a folder, got: {pointcloud}",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    # Default output path
    if output is None:
        if pointcloud.is_dir():
            output = pointcloud.parent / f"{pointcloud.name}_pointclouds.blend"
        else:
            output = pointcloud.with_suffix(".blend")

    rotation_xyz = (rotation_x, rotation_y, rotation_z)

    # Reset to a clean scene
    typer.echo("Resetting scene...")
    reset_scene()
    ensure_object_mode()

    # Import each PLY
    imported: list[bpy.types.Object] = []
    for ply_path in ply_files:
        obj = import_pointcloud(ply_path, rotation_xyz=rotation_xyz, name="Pointcloud")
        imported.append(obj)

    # Summary
    typer.echo("-" * 50)
    typer.secho(f"✓ Imported {len(imported)} pointcloud(s):", fg=typer.colors.GREEN)
    for obj in imported:
        typer.echo(f"    {obj.name}")

    # Save
    save_blend_file(output)

    typer.echo("=" * 50)
    typer.secho("✨ Done!", fg=typer.colors.GREEN, bold=True)


@app.command()
def test_import(
    fbx_file: Path = typer.Argument(..., help="Path to the FBX file to test"),
) -> None:
    """Test importing an FBX file and report what's found.
    
    Example:
        python project2_ex1_fbx_tiktok_renderer.py test-import character.fbx
    """
    typer.secho("🔍 Testing FBX Import", fg=typer.colors.CYAN, bold=True)
    typer.echo("=" * 50)
    
    # Reset scene
    typer.echo("Resetting scene...")
    reset_scene()
    ensure_object_mode()
    
    # Import FBX
    imported_objects = import_fbx(fbx_file)
    
    # Report findings
    typer.echo(f"\n📦 Imported {len(imported_objects)} objects:")
    for obj in imported_objects:
        typer.echo(f"  - {obj.name} (type: {obj.type})")
    
    # Find armature
    armature = find_armature(imported_objects)
    if armature:
        typer.secho(f"\n✓ Found armature: {armature.name}", fg=typer.colors.GREEN)
        
        # Check for animation
        if armature.animation_data and armature.animation_data.action:
            action = armature.animation_data.action
            start, end = action.frame_range
            typer.echo(f"  Animation: frames {int(start)} - {int(end)}")
            typer.echo(f"  Duration: {int(end - start)} frames")
        else:
            typer.secho("  ⚠ No animation data found", fg=typer.colors.YELLOW)
        
        # Check for target bone
        if TARGET_BONE_NAME in armature.pose.bones:
            typer.secho(f"  ✓ Found target bone: {TARGET_BONE_NAME}", fg=typer.colors.GREEN)
        else:
            typer.secho(f"  ⚠ Target bone not found: {TARGET_BONE_NAME}", fg=typer.colors.YELLOW)
            typer.echo(f"  Available bones ({len(armature.pose.bones)}):")
            for bone in list(armature.pose.bones)[:10]:  # Show first 10
                typer.echo(f"    - {bone.name}")
            if len(armature.pose.bones) > 10:
                typer.echo(f"    ... and {len(armature.pose.bones) - 10} more")
    else:
        typer.secho("\n⚠ No armature found", fg=typer.colors.YELLOW)
    
    typer.echo("=" * 50)
    typer.secho("✓ Test complete", fg=typer.colors.GREEN)


@app.command()
def test_template(
    blend_file: Path = typer.Argument(..., help="Path to the blend file template"),
    fbx_file: Path = typer.Argument(..., help="Path to the FBX file to import"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output .blend file path"),
) -> None:
    """Test loading a blend file template and importing an FBX into it.
    
    Example:
        python project2_ex1_fbx_tiktok_renderer.py test-template scene.blend character.fbx
        python project2_ex1_fbx_tiktok_renderer.py test-template scene.blend character.fbx --output result.blend
    """
    typer.secho("🎬 Testing Template Loading", fg=typer.colors.CYAN, bold=True)
    typer.echo("=" * 50)
    
    # Step 1: Load blend file
    typer.echo("\n1. Loading blend template...")
    load_blend_file(blend_file)
    
    # Report what's in the scene
    typer.echo(f"\n📦 Template contains {len(bpy.data.objects)} objects:")
    for obj in list(bpy.data.objects)[:10]:  # Show first 10
        typer.echo(f"  - {obj.name} (type: {obj.type})")
    if len(bpy.data.objects) > 10:
        typer.echo(f"  ... and {len(bpy.data.objects) - 10} more")
    
    # Step 2: Import FBX
    typer.echo(f"\n2. Importing FBX: {fbx_file}")
    imported_objects = import_fbx(fbx_file)
    typer.secho(f"✓ Imported {len(imported_objects)} new objects", fg=typer.colors.GREEN)
    
    # Step 3: Verify the scene
    typer.echo(f"\n3. Verifying combined scene...")
    typer.echo(f"Total objects in scene: {len(bpy.data.objects)}")
    
    # Find armature in imported objects
    armature = find_armature(imported_objects)
    if armature:
        typer.secho(f"✓ Found imported armature: {armature.name}", fg=typer.colors.GREEN)
        if armature.animation_data and armature.animation_data.action:
            action = armature.animation_data.action
            start, end = action.frame_range
            typer.echo(f"  Animation: frames {int(start)} - {int(end)}")
    
    # Step 4: Save if requested
    if output:
        typer.echo(f"\n4. Saving result...")
        save_blend_file(output)
    else:
        typer.echo("\n4. Not saving (use --output to save)")
    
    typer.echo("=" * 50)
    typer.secho("✓ Test complete", fg=typer.colors.GREEN)


@app.command()
def create(
    fbx_file: Path = typer.Argument(..., help="Path to the FBX file to import"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output .blend file path"),
    bone: str = typer.Option(TARGET_BONE_NAME, "--bone", "-b", help="Target bone name for camera tracking"),
    start_frame: int = typer.Option(1, "--start", "-s", help="Animation start frame"),
    end_frame: Optional[int] = typer.Option(None, "--end", "-e", help="Animation end frame (defaults to last frame of armature animation)"),
    no_lights: bool = typer.Option(False, "--no-lights", help="Skip adding studio lights"),
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

    # Determine end frame if not specified
    if end_frame is None:
        if armature and armature.animation_data and armature.animation_data.action:
            end_frame = int(armature.animation_data.action.frame_range[1])
            typer.secho(
                f"✓ Using armature animation end frame: {end_frame}",
                fg=typer.colors.GREEN,
            )
        else:
            end_frame = 250  # Fallback default
            typer.secho(
                f"⚠ No animation data found, using default end frame: {end_frame}",
                fg=typer.colors.YELLOW,
            )

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


@app.command()
def render(
    blend_file: Path = typer.Argument(..., help="Path to the blend file to render"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output MP4 file path"),
    fps: int = typer.Option(24, "--fps", help="Frames per second for output video"),
    quality: str = typer.Option("high", "--quality", "-q", help="Quality preset: high, medium, or low"),
    frame_start: Optional[int] = typer.Option(None, "--start", "-s", help="Start frame (defaults to scene start)"),
    frame_end: Optional[int] = typer.Option(None, "--end", "-e", help="End frame (defaults to scene end)"),
) -> None:
    """Render a blend file animation to MP4.
    
    This command loads a blend file and renders the animation directly
    to MP4 using Blender's built-in FFmpeg encoder.
    
    Examples:
        python project2_ex1_fbx_tiktok_renderer.py render scene.blend
        python project2_ex1_fbx_tiktok_renderer.py render scene.blend -o output.mp4
        python project2_ex1_fbx_tiktok_renderer.py render scene.blend -q medium --fps 30
        python project2_ex1_fbx_tiktok_renderer.py render scene.blend --start 1 --end 100
    """
    typer.secho("🎬 Rendering Animation to MP4", fg=typer.colors.CYAN, bold=True)
    typer.echo("=" * 50)
    
    # Default output path
    if output is None:
        output = blend_file.with_suffix(".mp4")
    
    # Load the blend file
    typer.echo(f"Loading blend file: {blend_file}")
    load_blend_file(blend_file)
    
    # Verify we have a camera
    if bpy.context.scene.camera is None:
        typer.secho("Error: Scene has no active camera!", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    
    # Render to MP4
    typer.echo(f"\nOutput file: {output}")
    render_to_mp4(
        output_path=output,
        fps=fps,
        quality=quality,
        frame_start=frame_start,
        frame_end=frame_end,
    )
    
    typer.echo("=" * 50)
    typer.secho("✨ Render complete!", fg=typer.colors.GREEN, bold=True)


if __name__ == "__main__":
    app()
