# Week 1 — Technical Direction Foundations

to bootstrap the python environment on MacOS run: 
``` shell
curl -fsSL https://raw.githubusercontent.com/michaelgold/buildbpy/refs/heads/main/bootstrap-osx.sh | bash
```

to boostrap the environment on Windows run:

```powershell
iwr -Uri https://raw.githubusercontent.com/michaelgold/buildbpy/refs/heads/main/bootstrap-windows.ps1 -OutFile bootstrap-windows.ps1; Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process; .\bootstrap-windows.ps1
```

to activate the environment run:
``` shell
  source .venv/bin/activate
```

Week 1 introduces students to Blender automation fundamentals and how Technical Directors translate pipeline requirements into reproducible scripts. Each exercise mirrors the course focus on rapid scene setup, lighting, and rendering automation. Scripts are intended to run both from Blender's Scripting workspace and from the command line using `blender --background --python <script.py>`.

## Prerequisites
- Blender 4.x installed locally.
- Python 3.10+ environment with `bpy` available (the class virtual environment supplies this when running headless).
- Launch Blender once and set default unit scale to Metric for consistent results.

## Exercise 1 — Scene Bootstrap + Cube Animation (`week1_ex1_scene_basics.py`)
Goal: Reinforce `bpy` basics by cleaning the scene, building simple geometry, animating the classic traveling cube, and persisting the result to `week1ex1.blend`.

Key beats:
1. Reset to factory settings for a predictable start state.
2. Add a ground plane, default cube, and a neutral material.
3. Keyframe the cube at frames 1, 15, and 30 following the "Animating a Cube" plan from the sample.
4. Save the generated file next to the script.

Run options:
- Blender UI: Scripting workspace → Open `week1_ex1_scene_basics.py` → Run Script.
- Command line: `blender --background --python week1_ex1_scene_basics.py`.

## Exercise 2 — Automated Camera + Lighting Rig (`week1_ex2_camera_lighting.py`)
Goal: Expand automation with helper functions that add a camera, a sun light, and a fill light, then render a still frame and save to `week1ex2.blend`.

Key beats:
1. Reuse the clean-scene helper for determinism.
2. Procedurally place a hero object (Suzanne) plus a reflective floor.
3. Create a cinematic camera and two lighting presets controlled via code.
4. Set the render engine to Cycles, configure output paths, and trigger a single frame render.
5. Save the `.blend` for later inspection.

Run options mirror Exercise 1; adjust the script name in the command.

## Exercise 3 — Character Import Stub + Batch Render (`week1_ex3_character_stub.py`)
Goal: Emulate HW1 by preparing a placeholder "character import" automation that students can later point at supplied assets. The script still runs standalone by falling back to primitives and saving to `week1ex3.blend`.

Key beats:
1. Parameterize the character asset path (defaults to a `placeholder_character.fbx` next to the script) and detect whether it exists.
2. If the asset is missing, spawn a proxy mesh so the pipeline can still be validated.
3. Build camera + keyframes via helper functions and mimic the provided "Automated Character Import" brief (camera offsets, consistent lighting, render output).
4. Save the `.blend` and emit console instructions reminding students to swap in their actual character.

## Deliverables
- Upload rendered frames plus the produced `.blend` files (`week1ex1.blend`, `week1ex2.blend`, `week1ex3.blend`) to GitLab.
- Document any deviations or experimentation in your homework log.
