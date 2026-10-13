# MalGuard GitHub visual identity

The original logo comes from the official website repository:
https://github.com/MalGuard/malguard.github.io/blob/main/assets/fusion/assets/malguard-logo.svg

Its SVG paths and original colors are preserved. The animation extrudes those paths in Blender, adds lighting and orbiting rings, and renders a seamless six-second loop. No stock logo or third-party image service is used.

Colors: official royal blue `#2F6BFF`, official cyan `#00bdf4`, midnight `#080e1f`, indigo `#16112d`, and accent violet `#9a6bff`.

## Regeneration

Prerequisites: Blender 4.3+, Python 3, Pillow, NumPy, FFmpeg, and DejaVu Sans fonts.

1. Run `blender -b -t 8 -P tools/render_emblem.py` from your checkout.
2. Run `python tools/build_assets.py`.
3. Optional MP4: `ffmpeg -framerate 15 -i render/hero-%03d.png -c:v libx264 -pix_fmt yuv420p -movflags +faststart assets/malguard-3d.mp4`.

The README uses a static poster for `prefers-reduced-motion: reduce`. Decorative SVG animation also respects that preference where supported. All linked cards carry descriptive alternative text. Graphics work without JavaScript, external fonts or third-party statistics servers.

## Account settings

These fields require GitHub's account settings UI; repository tools cannot update them:

- Profile picture: `assets/avatar-3d.png` (the official logo).
- Bio: `Creator of MalGuard · Defensive engineering for safer game mods · Inspect before you trust.`
- Website: `https://malguard.github.io/`
- Suggested pins: `malguard-core`, `malguard.github.io`, `GTA-guard.github.io`, `MalGuard`.
- Repository social preview: `assets/social-preview.png`.

GitHub controls the surrounding page background and theme. Dark backgrounds live inside the profile graphics. GitHub profile pictures are static; the animated 3D logo belongs in the README.
