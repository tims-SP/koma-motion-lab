extends Node2D

var character: GDCubismUserModel
var tick: float = 0.0

func _ready() -> void:
    if OS.get_environment("GODOT004_BG_WHITE") == "1":
        RenderingServer.set_default_clear_color(Color(0.98, 0.98, 0.98, 1.0))
        print("GODOT004_WHITE_BACKGROUND_ENABLED")
    print("GODOT002_PHASE_BEFORE_CONSTRUCT")
    character = GDCubismUserModel.new()
    print("GODOT002_PHASE_AFTER_CONSTRUCT")
    add_child(character)
    print("GODOT002_PHASE_AFTER_ADD_CHILD")
    if OS.get_environment("GODOT002_CONSTRUCT_ONLY") == "1":
        print("GODOT002_CONSTRUCT_ONLY_PASS")
        get_tree().quit()
        return
    if OS.get_environment("GODOT002_DISABLE_MOTIONS") == "1":
        character.load_motions = false
        print("GODOT002_PRELOAD_MOTIONS_DISABLED")
    print("GODOT002_PHASE_BEFORE_ASSETS")
    character.assets = "res://assets/301003_x/301003_x.model3.json"
    print("GODOT002_PHASE_AFTER_ASSETS")
    print("GODOT002_MOC3_SOURCE=301003_x")
    var canvas: Dictionary = character.get_canvas_info()
    if canvas.is_empty() or not canvas.has("size_in_pixels"):
        push_error("GODOT002_MODEL_LOAD_FAILED")
        get_tree().quit(24)
        return
    var dims: Vector2 = canvas["size_in_pixels"]
    var factor: float = min(750.0 / max(dims.x, 1.0), 495.0 / max(dims.y, 1.0))
    character.position = Vector2(480, 270)
    character.scale = Vector2.ONE * factor
    if OS.get_environment("GODOT003_SWEEP") == "1":
        var sweep_zoom: float = float(OS.get_environment("GODOT003_SWEEP_ZOOM"))
        var sweep_shift: float = float(OS.get_environment("GODOT003_SWEEP_SHIFT_Y"))
        character.scale *= sweep_zoom
        character.position.y += sweep_shift
        print("GODOT003_CAMERA_SWEEP_APPLIED ZOOM=", sweep_zoom, " SHIFT_Y=", sweep_shift)
    var zenv := OS.get_environment("GODOT002_ZOOM")
    if not zenv.is_empty() and (OS.get_environment("GODOT002_DISABLE_MOTIONS") != "1" or OS.get_environment("GODOT002_FRAMED_STATIC") == "1"):
        var diagnostic_zoom: float = clampf(float(zenv), 1.0, 2.75)
        var diagnostic_dx: float = float(OS.get_environment("GODOT002_SHIFT_X"))
        var diagnostic_dy: float = float(OS.get_environment("GODOT002_SHIFT_Y"))
        character.scale *= diagnostic_zoom
        character.position += Vector2(diagnostic_dx, diagnostic_dy)
        print("GODOT002_DIAGNOSTIC_AUTOFRAME=", diagnostic_zoom, " OFFSET=", Vector2(diagnostic_dx, diagnostic_dy))
    if OS.get_environment("GODOT004_HIRES") == "1":
        character.position *= 2.0
        character.scale *= 2.0
        print("GODOT004_HIRES_2X_APPLIED")
    print("GODOT002_MODEL_CANVAS=", dims, " SCALE=", factor)
    if OS.get_environment("GODOT002_DISABLE_MOTIONS") == "1":
        print("GODOT002_STATIC_MODEL_LOAD_PASS")
        return
    var motions: Dictionary = character.get_motions()
    print("GODOT002_MOTIONS=", JSON.stringify(motions))
    var motion_name := OS.get_environment("GODOT004_MOTION_GROUP")
    if motion_name.is_empty():
        motion_name = "nod"
    if motion_name != "nod" and motion_name != "idle" and motion_name != "face_idle":
        push_error("GODOT004_UNSUPPORTED_MOTION_GROUP")
        get_tree().quit(26)
        return
    if not motions.has(motion_name):
        push_error("GODOT004_MOTION_GROUP_MISSING=" + motion_name)
        get_tree().quit(25)
        return
    character.playback_process_mode = GDCubismUserModel.IDLE
    character.start_motion(motion_name, 0, GDCubismUserModel.PRIORITY_FORCE)
    print("GODOT002_REAL_MOTION_STARTED")
    print("GODOT004_REAL_MOTION_GROUP_STARTED=", motion_name)

func _process(delta: float) -> void:
    tick += delta
