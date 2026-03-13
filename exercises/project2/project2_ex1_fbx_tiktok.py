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
CAMERA_HEIGHT_OFFSET = 0.0  # Camera at same height as tracked bone
CAMERA_LOOK_UP_OFFSET = 0.3  # Look slightly above tracked bone for better full-body framing
CAMERA_VERTICAL_FILL = 0.72  # Portion of frame height the character should occupy
CAMERA_HORIZONTAL_FILL = 0.65  # Portion of frame width the character should occupy
CAMERA_DISTANCE_PADDING = 1.1  # Extra breathing room around the character
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


def place_character(
    imported_objects: list[bpy.types.Object],
    location: tuple[float, float, float] = (0.0, 0.0, 0.0),
    rotation_deg: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> Optional[bpy.types.Object]:
    """Set location and rotation on the root/armature of an imported FBX character.

    Returns the armature (or first object if no armature found).
    """
    armature = find_armature(imported_objects)
    root = armature if armature else (imported_objects[0] if imported_objects else None)
    if root is None:
        typer.secho("Warning: No objects to place for character.", fg=typer.colors.YELLOW)
        return None

    root.location = location
    root.rotation_euler = (
        math.radians(rotation_deg[0]),
        math.radians(rotation_deg[1]),
        math.radians(rotation_deg[2]),
    )
    typer.secho(
        f"✓ Placed '{root.name}' at {location}, rotation={rotation_deg[0]}°, "
        f"{rotation_deg[1]}°, {rotation_deg[2]}°",
        fg=typer.colors.GREEN,
    )
    return root


def import_and_place_fbx(
    fbx_path: Path,
    location: tuple[float, float, float] = (0.0, 0.0, 0.0),
    rotation_deg: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> list[bpy.types.Object]:
    """Import an FBX and immediately place it at the given location/rotation."""
    imported = import_fbx(fbx_path)
    place_character(imported, location=location, rotation_deg=rotation_deg)
    return imported



def reset_scene() -> None:
    """Reset to a clean empty scene — no default cube, camera, or light."""
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


def resolve_tracking_bone_name(
    armature: bpy.types.Object,
    bone_name: Optional[str],
) -> Optional[str]:
    """Resolve the requested tracking bone to the actual FBX armature bone name."""
    if bone_name is None:
        return None

    if bone_name in armature.pose.bones:
        return bone_name

    target_suffix = bone_name.split(":")[-1].lower()
    for candidate in armature.pose.bones.keys():
        if candidate.split(":")[-1].lower() == target_suffix:
            return candidate

    for candidate in ("Hips", "mixamorig:Hips", "mixamorig1:Hips", "Pelvis", "pelvis"):
        if candidate in armature.pose.bones:
            return candidate

    return None


def get_target_world_location(
    armature: bpy.types.Object, bone_name: str
) -> tuple[float, float, float]:
    """Get world location of a bone in the armature.

    If the bone is not found, estimates hip height by adding ~0.9 m in world Z
    to the armature root (which is typically at foot level after Mixamo import).
    """
    if bone_name in armature.pose.bones:
        bone = armature.pose.bones[bone_name]
        matrix = armature.matrix_world @ bone.matrix
        return tuple(matrix.translation)

    # Fallback: armature root is at foot level — add ~0.9 m to estimate hips
    root = tuple(armature.matrix_world.translation)
    return (root[0], root[1], root[2] + 0.9)


def get_character_mesh_objects(
    character_objects: list[bpy.types.Object],
) -> list[bpy.types.Object]:
    """Return mesh objects used to frame the character."""
    return [obj for obj in character_objects if obj.type == "MESH"]


def get_object_world_bounds(
    obj: bpy.types.Object,
    depsgraph: bpy.types.Depsgraph,
) -> Optional[tuple[float, float, float, float, float, float]]:
    """Return evaluated world-space bounds for an object as min/max XYZ."""
    obj_eval = obj.evaluated_get(depsgraph)
    bound_box = getattr(obj_eval, "bound_box", None)
    if not bound_box:
        return None

    world_corners = [obj_eval.matrix_world @ Vector(corner) for corner in bound_box]
    xs = [corner.x for corner in world_corners]
    ys = [corner.y for corner in world_corners]
    zs = [corner.z for corner in world_corners]
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


def get_character_frame_bounds(
    character_objects: list[bpy.types.Object],
    depsgraph: bpy.types.Depsgraph,
) -> Optional[dict[str, float]]:
    """Return combined evaluated bounds for the full character on the current frame."""
    mesh_objects = get_character_mesh_objects(character_objects)
    if not mesh_objects:
        return None

    bounds = [get_object_world_bounds(obj, depsgraph) for obj in mesh_objects]
    bounds = [item for item in bounds if item is not None]
    if not bounds:
        return None

    min_x = min(item[0] for item in bounds)
    max_x = max(item[1] for item in bounds)
    min_y = min(item[2] for item in bounds)
    max_y = max(item[3] for item in bounds)
    min_z = min(item[4] for item in bounds)
    max_z = max(item[5] for item in bounds)

    return {
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y,
        "min_z": min_z,
        "max_z": max_z,
        "center_x": (min_x + max_x) / 2,
        "center_y": (min_y + max_y) / 2,
        "center_z": (min_z + max_z) / 2,
        "width": max_x - min_x,
        "depth": max_y - min_y,
        "height": max_z - min_z,
    }


def analyze_character_framing(
    camera: bpy.types.Object,
    target: bpy.types.Object,
    character_objects: list[bpy.types.Object],
    bone_name: Optional[str],
    frame_start: int,
    frame_end: int,
) -> dict[str, object]:
    """Sample animated bounds to derive a camera distance that fits the full body."""
    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()
    samples: dict[int, dict[str, float]] = {}
    max_height = 0.0
    max_width = 0.0
    center_offset_z_total = 0.0
    sample_count = 0

    for frame in range(frame_start, frame_end + 1, FRAME_STEP):
        scene.frame_set(frame)
        depsgraph.update()

        if target.type == "ARMATURE" and bone_name:
            target_loc = get_target_world_location(target, bone_name)
        else:
            target_loc = tuple(target.matrix_world.translation)

        bounds = get_character_frame_bounds(character_objects, depsgraph)
        if bounds is None:
            continue

        samples[frame] = bounds
        max_height = max(max_height, bounds["height"])
        max_width = max(max_width, bounds["width"])
        center_offset_z_total += bounds["center_z"] - target_loc[2]
        sample_count += 1

    vertical_angle = camera.data.angle_y
    horizontal_angle = camera.data.angle_x

    vertical_distance = CAMERA_DISTANCE
    horizontal_distance = CAMERA_DISTANCE
    if max_height > 0:
        vertical_distance = (max_height / 2) / math.tan(vertical_angle / 2)
        vertical_distance /= CAMERA_VERTICAL_FILL
    if max_width > 0:
        horizontal_distance = (max_width / 2) / math.tan(horizontal_angle / 2)
        horizontal_distance /= CAMERA_HORIZONTAL_FILL

    camera_distance = max(CAMERA_DISTANCE, vertical_distance, horizontal_distance)
    camera_distance *= CAMERA_DISTANCE_PADDING
    fallback_center_offset_z = (
        center_offset_z_total / sample_count if sample_count else CAMERA_HEIGHT_OFFSET
    )

    typer.echo(
        "  Adaptive framing: "
        f"height={max_height:.2f}m width={max_width:.2f}m distance={camera_distance:.2f}m"
    )

    return {
        "camera_distance": camera_distance,
        "fallback_center_offset_z": fallback_center_offset_z,
        "samples": samples,
    }


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
    character_objects: Optional[list[bpy.types.Object]] = None,
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
    character_objects = character_objects or [target]
    resolved_bone_name = bone_name

    if target.type == "ARMATURE" and bone_name:
        resolved_bone_name = resolve_tracking_bone_name(target, bone_name)
        if resolved_bone_name:
            if resolved_bone_name == bone_name:
                typer.echo(f"  Tracking movement from bone '{resolved_bone_name}'")
            else:
                typer.echo(
                    f"  Tracking movement from bone '{resolved_bone_name}' (resolved from '{bone_name}')"
                )
        else:
            typer.secho(
                f"  ⚠ Bone '{bone_name}' not found — falling back to estimated hip position",
                fg=typer.colors.YELLOW,
            )

    framing = analyze_character_framing(
        camera,
        target,
        character_objects,
        resolved_bone_name,
        frame_start,
        frame_end,
    )
    camera_distance = float(framing["camera_distance"])
    fallback_center_offset_z = float(framing["fallback_center_offset_z"])
    frame_samples = framing["samples"]

    # Bake keyframes
    for frame in range(frame_start, frame_end + 1, FRAME_STEP):
        scene.frame_set(frame)

        # Get target location
        if target.type == "ARMATURE" and resolved_bone_name:
            target_loc = get_target_world_location(target, resolved_bone_name)
        else:
            target_loc = tuple(target.matrix_world.translation)

        bounds = frame_samples.get(frame)
        focus_x = bounds["center_x"] if bounds else target_loc[0]
        focus_y = target_loc[1]
        focus_z = bounds["center_z"] if bounds else (target_loc[2] + fallback_center_offset_z)

        # Position camera behind the character at a distance derived from full-body size
        camera.location = (
            focus_x,
            focus_y - camera_distance,
            focus_z,
        )

        # Keep the full body centered for the duration of the animation
        look_at = (
            focus_x,
            focus_y,
            focus_z + CAMERA_LOOK_UP_OFFSET,
        )
        direction = Vector(
            (
                look_at[0] - camera.location[0],
                look_at[1] - camera.location[1],
                look_at[2] - camera.location[2],
            )
        )

        # Calculate rotation to look at target
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


BLENDER_BIN = Path("/Applications/Blender.app/Contents/MacOS/Blender")


def setup_render_output(
    output_path: Path,
    fmt: str = "mp4",
    frame_start: int = 1,
    frame_end: int = 250,
) -> None:
    """Store frame range and output path in the scene (baked into .blend).

    FFmpeg / H264 settings are applied later by the injected render script
    running inside the full Blender binary, which has FFmpeg support.
    """
    scene = bpy.context.scene
    scene.frame_start = frame_start
    scene.frame_end = frame_end
    scene.render.filepath = str(output_path)
    scene.render.image_settings.file_format = "PNG"  # placeholder; overridden at render time

    typer.secho(
        f"✓ Frame range set: {frame_start}–{frame_end}  output: {output_path}",
        fg=typer.colors.GREEN,
    )


def render_via_blender(
    blend_path: Path,
    output_path: Path,
    fmt: str = "mp4",
    frame_start: int = 1,
    frame_end: int = 250,
    single_frame: bool = False,
) -> None:
    """Render natively inside the full Blender binary.

    Writes a small Python setup script and passes it to Blender via
    ``--python`` so that FFmpeg / H264 settings are applied the same way
    as ``render_to_mp4()`` in ``project2_ex1_fbx_tiktok_renderer.py``
    — i.e. ``media_type = 'VIDEO'`` first, then ``file_format = 'FFMPEG'``.
    """
    import subprocess
    import tempfile

    if not BLENDER_BIN.exists():
        typer.secho(f"Error: Blender binary not found at {BLENDER_BIN}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if fmt.lower() == "png":
        render_call = f"scene.frame_set({frame_start})\nbpy.ops.render.render(write_still=True)"
        format_block = "scene.render.image_settings.file_format = 'PNG'"
    else:
        render_call = (
            f"scene.frame_set({frame_start})\nbpy.ops.render.render(write_still=True)"
            if single_frame
            else "bpy.ops.render.render(animation=True, write_still=False)"
        )
        # Mirror render_to_mp4() from project2_ex1_fbx_tiktok_renderer.py:
        # set media_type = 'VIDEO' *before* file_format = 'FFMPEG' — this is
        # the key step that enables FFMPEG inside the full Blender binary.
        format_block = "\n".join([
            "scene.render.image_settings.media_type = 'VIDEO'",
            "scene.render.image_settings.file_format = 'FFMPEG'",
            "scene.render.ffmpeg.format = 'MPEG4'",
            "scene.render.ffmpeg.codec = 'H264'",
            "scene.render.ffmpeg.constant_rate_factor = 'HIGH'",
            "scene.render.ffmpeg.ffmpeg_preset = 'GOOD'",
            "scene.render.ffmpeg.audio_codec = 'AAC'",
            "scene.render.ffmpeg.audio_bitrate = 192",
        ])

    script = (
        "import bpy\n"
        "scene = bpy.context.scene\n"
        f"{format_block}\n"
        f"scene.render.filepath = r'{output_path}'\n"
        f"scene.frame_start = {frame_start}\n"
        f"scene.frame_end = {frame_end}\n"
        f"{render_call}\n"
    )

    import re

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
        tmp.write(script)
        script_path = tmp.name

    total_frames = frame_end - frame_start + 1
    cmd = [str(BLENDER_BIN), "--background", str(blend_path), "--python", script_path]
    typer.echo("Launching Blender render (native FFmpeg H264)...")

    last_pct = -1
    returncode = 0
    with subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    ) as proc:
        for line in proc.stdout:
            m = re.search(r"Video append frame (\d+)", line)
            if m:
                frame_num = int(m.group(1))
                pct = int((frame_num - frame_start + 1) / total_frames * 100)
                if pct != last_pct:  # only reprint when percentage changes
                    last_pct = pct
                    bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
                    print(f"\r  [{bar}] {pct:3d}%  frame {frame_num}/{frame_end}", end="", flush=True)
        returncode = proc.wait()

    print()  # newline after progress bar
    Path(script_path).unlink(missing_ok=True)

    if returncode != 0:
        typer.secho("Error: Blender render exited with errors.", fg=typer.colors.RED)
        raise typer.Exit(code=returncode)
    typer.secho("✓ Render complete", fg=typer.colors.GREEN)
    if output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        typer.echo(f"  File size: {size_mb:.2f} MB")


def save_blend_file(output_path: Optional[Path] = None) -> None:

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
    setup_camera_tracking(
        camera,
        target,
        imported_objects,
        target_bone,
        start_frame,
        end_frame,
    )

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
    character: Annotated[
        Optional[Path],
        typer.Option("--character", "-c", help="Path to a single character FBX file"),
    ] = None,
    character_dir: Annotated[
        Optional[Path],
        typer.Option("--character-dir", help="Directory of FBX files to import all characters"),
    ] = None,
    char_location: Annotated[
        Optional[list[float]],
        typer.Option("--char-location", help="Character location X Y Z (pass three times, default 0 0 0)"),
    ] = None,
    char_rotation: Annotated[
        Optional[list[float]],
        typer.Option("--char-rotation", help="Character rotation in degrees X Y Z (pass three times, default 0 0 0)"),
    ] = None,
    render: Annotated[
        bool,
        typer.Option("--render", help="Render after scene setup"),
    ] = False,
    render_format: Annotated[
        str,
        typer.Option("--render-format", help="Output format: mp4 or png"),
    ] = "mp4",
    single_frame: Annotated[
        bool,
        typer.Option("--single-frame", help="Render a single frame instead of full animation"),
    ] = False,
    start_frame: Annotated[
        int,
        typer.Option("--start-frame", help="Animation start frame"),
    ] = 1,
    end_frame: Annotated[
        int,
        typer.Option("--end-frame", help="Animation end frame"),
    ] = 250,
) -> None:
    """Import one or all .ply pointclouds, apply rotation, name them 'Pointcloud',
    and attach the RadianceField geometry node group. Optionally import character FBX(s).

    Examples:
        python script.py import-pointcloud --pointcloud pointclouds/Hydrant.ply --rotation 0 --rotation 0 --rotation 45
        python script.py import-pointcloud --pointcloud-dir pointclouds/ --character-dir characters/
        python script.py import-pointcloud --pointcloud pointclouds/Hydrant.ply --character characters/michelle-hiphop.fbx --render
        python script.py import-pointcloud --pointcloud pointclouds/Hydrant.ply --character characters/michelle-hiphop.fbx --render --single-frame
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

    # --- Character import ---
    fbx_files: list[Path] = []
    if character is not None:
        fbx_files = [character]
    elif character_dir is not None:
        character_dir = character_dir.expanduser().resolve()
        fbx_files = sorted(character_dir.glob("*.fbx"))
        if not fbx_files:
            typer.secho(f"Warning: No .fbx files found in {character_dir}", fg=typer.colors.YELLOW)

    imported_character_objects: list[bpy.types.Object] = []
    if fbx_files:
        # Parse character location / rotation
        char_loc: tuple[float, float, float]
        char_rot: tuple[float, float, float]
        if char_location is not None:
            if len(char_location) != 3:
                typer.secho("Error: --char-location requires exactly 3 values.", fg=typer.colors.RED)
                raise typer.Exit(code=1)
            char_loc = (char_location[0], char_location[1], char_location[2])
        else:
            char_loc = (0.0, -1.3, -1.5)

        if char_rotation is not None:
            if len(char_rotation) != 3:
                typer.secho("Error: --char-rotation requires exactly 3 values.", fg=typer.colors.RED)
                raise typer.Exit(code=1)
            char_rot = (char_rotation[0] + 90.0, char_rotation[1], char_rotation[2])
        else:
            char_rot = (90.0, 0.0, 0.0)

        typer.echo(f"Importing {len(fbx_files)} character(s)...")
        for fbx_file in fbx_files:
            imported_character_objects = import_and_place_fbx(
                fbx_file,
                location=char_loc,
                rotation_deg=char_rot,
            )

    typer.echo("7. Saving blend file...")
    # Auto-generate name from character + pointcloud stems if no explicit output given
    char_stem = fbx_files[0].stem if fbx_files else "scene"
    pc_stem = ply_files[0].stem if ply_files else "pointcloud"
    base_name = f"{char_stem}_{pc_stem}"
    if output is None:
        output = Path.cwd() / f"{base_name}.blend"
    save_blend_file(output)

    # --- Render ---
    if render:
        render_output_path: Path
        if render_format.lower() == "png":
            render_output_path = Path.cwd() / "renders" / f"{base_name}_"
        else:
            render_output_path = Path.cwd() / f"{base_name}.mp4"
        render_output_path.parent.mkdir(parents=True, exist_ok=True)

        # Set up TikTok camera and tracking, then re-save blend before rendering
        armature = find_armature(list(bpy.data.objects))
        if armature:
            typer.echo("Setting up TikTok camera for render...")
            camera = create_tiktok_camera()
            setup_camera_tracking(
                camera,
                armature,
                imported_character_objects,
                TARGET_BONE_NAME,
                start_frame,
                end_frame,
            )
            add_studio_lighting()

        typer.echo(f"8. Configuring render output: {render_output_path}")
        setup_render_output(render_output_path, fmt=render_format, frame_start=start_frame, frame_end=end_frame)

        # Re-save blend with render settings baked in
        save_blend_file(output)

        typer.echo("9. Launching Blender for render...")
        render_via_blender(
            blend_path=output,
            output_path=render_output_path,
            fmt=render_format,
            frame_start=start_frame,
            frame_end=end_frame,
            single_frame=single_frame,
        )
    else:
        typer.echo("Skipping render (use --render to render).")

    typer.echo("=" * 50)
    typer.secho("✨ Pointcloud import complete!", fg=typer.colors.GREEN, bold=True)
    typer.echo(f"Imported {len(ply_files)} pointcloud(s) with rotation {rot}")
    typer.echo(f"Bounding box: {bbox}")
    if fbx_files:
        typer.echo(f"Imported {len(fbx_files)} character(s) at location {char_loc}, rotation {char_rot}")
    typer.echo(f"Saved: {output}")
    if render:
        typer.echo(f"Render output: {render_output_path}")


if __name__ == "__main__":
    app()
