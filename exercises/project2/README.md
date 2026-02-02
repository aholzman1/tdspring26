# Week 2 — Python + Blender Scripting Ramp-Up

Week 2 drills into modular `bpy` tooling: functions, helpers, multi-camera orchestration, and debugging patterns. Each exercise layers on top of Week 1 work, encouraging Technical Directors to think in reusable building blocks while still delivering concrete `.blend` hand-ins (`week2ex1.blend`, `week2ex2.blend`, `week2ex3.blend`).

## Prerequisites
- Complete the Week 1 exercises and keep the same project checkout.
- Confirm Blender 4.x can find the class virtual environment so `bpy` is available when running headless.
- Keep the HackMD notes handy for reference on logging and Git workflows.

## Exercise 1 — Multi-Camera Lighting Presets (`week2_ex1_multi_cam.py`)
Goal: Iterate on the lighting automation by generating multiple camera + light presets from a configuration table, batch rendering each shot, and saving to `week2ex1.blend`.

Highlights:
1. Define a list of camera dictionaries containing position, lens, and exposure tweaks.
2. Create two lighting modes (Studio vs. Rim) and toggle them per shot.
3. Loop through the presets, repositioning the rig, rendering to `week2_ex1_<camera>.png`, and logging progress.

Run from Blender's Scripting workspace or via `blender --background --python week2_ex1_multi_cam.py`.

## Exercise 2 — Camera Follow Automation (`week2_ex2_camera_follow.py`)
Goal: Translate the "Animating an Avatar" prompt into production-ready tooling that can target either the default `Armature` or a generated stand-in. The script bakes keyframes every 10 frames, keeps the camera 3 m behind and 3 m above, and saves to `week2ex2.blend`.

Highlights:
1. Detect whether `Armature` exists; if not, create an animated proxy rig.
2. Wrap the look-at math in a helper so the camera always tracks the hips bone or proxy target.
3. Expose frame range and offsets at the top of the script to encourage parameter tuning.

## Exercise 3 — CLI Pipeline Driver (`week2_ex3_pipeline_driver.py`)
Goal: Evaluate a "new technology stack" mindset by wiring a command-line interface that accepts preset names (e.g., `turntable`, `closeup`), builds the matching scene, and exports both renders and the `.blend` file.

Highlights:
1. Use `argparse` to accept `--preset` and `--output` arguments so the tool can plug into future GitLab CI jobs.
2. Encapsulate scene-building logic into functions that can be unit tested or imported elsewhere.
3. Serialize the resulting scene to `week2ex3.blend` and optionally trigger renders based on the preset.

## Exercise 4 — FBX Import with TikTok Camera (`week2_ex4_fbx_tiktok.py`)
Goal: Build a modern CLI tool using `typer` that imports FBX files and creates a vertical TikTok-style camera (9:16 aspect ratio) that automatically follows animated characters.

Highlights:
1. Use `typer` for a rich CLI experience with type hints and automatic help generation.
2. Import FBX files and automatically detect armatures and animation data.
3. Create a vertical camera (1080x1920) with smooth tracking that follows a bone (e.g., `mixamorig:Hips`).
4. Bake keyframes for camera position and rotation to ensure smooth following throughout the animation.
5. Optional three-point studio lighting setup for professional-looking renders.

Run with:
```bash
blender --background --python week2_ex4_fbx_tiktok.py -- create path/to/character.fbx
blender --background --python week2_ex4_fbx_tiktok.py -- create character.fbx --output my_scene.blend --start 1 --end 120
```

As before, run any script in the UI or via the CLI. Remember to commit the resulting `.blend` files and renders to GitLab for feedback.
