"""House style for every sprite-stacked character.

Change a value here and every character rebuilt afterwards changes with it.
Keep these fixed across a game so all models look like they belong together.
"""

# --- volume ---------------------------------------------------------------
# One sprite pixel = one cube. A ~88px-tall sprite fits the default box.
GRID_W, GRID_H, GRID_D = 72, 90, 48      # x (left-right), y (top-down), z (back-front)

# --- lighting (baked into the cubes, so it turns with the model) ----------
LIGHT = (-0.45, -0.7, 0.55)   # from upper front left (x left, y up, z toward viewer)
AMBIENT = 0.5                 # brightness of a surface facing away from the light
DIFFUSE = 0.7                 # extra brightness for a surface facing the light
BAND = 0.15                   # shade step size: bold pixel-art bands on the body
SMOOTH_BAND = 0.05            # finer steps for large flat parts (brims, capes, shields)
NORMAL_BLUR = 1.4             # how rounded the surface lighting looks

# --- faces ----------------------------------------------------------------
FACE_PLATE = 5                # flatten the head this many cubes in front of its centre
EYE_DEPTH = 3                 # paint eyes this many cubes deep so they hold when turned
EYE_GAP = 2                   # inner eye column sits this many cubes from the face centre

# --- glowing parts (orbs, gems, magic) ------------------------------------
GLOW_MIN, GLOW_RANGE, GLOW_SPEC = 0.75, 0.35, 0.93
SPEC_COLOR = (255, 250, 255)

# --- previews and viewer --------------------------------------------------
CAMERA_TILT = 22              # degrees of look-down in previews and the viewer
PREVIEW_SCALE = 4             # screen pixels per cube in GIFs and sheets
TURNTABLE_FRAMES = 36
BACKGROUND = (24, 20, 40)
