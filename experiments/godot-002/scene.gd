extends Node2D

var character: GDCubismUserModel
var tick: float = 0.0

func _ready() -> void:
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
    var zenv := OS.get_environment("GODOT002_ZOOM")
    if not zenv.is_empty() and OS.get_environment("GODOT002_DISABLE_MOTIONS") != "1":
        var diagnostic_zoom: float = clampf(float(zenv), 1.0, 2.75)
        var diagnostic_dx: float = float(OS.get_environment("GODOT002_SHIFT_X"))
        var diagnostic_dy: float = float(OS.get_environment("GODOT002_SHIFT_Y"))
        character.scale *= diagnostic_zoom
        character.position += Vector2(diagnostic_dx, diagnostic_dy)
        print("GODOT002_DIAGNOSTIC_AUTOFRAME=", diagnostic_zoom, " OFFSET=", Vector2(diagnostic_dx, diagnostic_dy))
    print("GODOT002_MODEL_CANVAS=", dims, " SCALE=", factor)
    if OS.get_environment("GODOT002_DISABLE_MOTIONS") == "1":
        print("GODOT002_STATIC_MODEL_LOAD_PASS")
        return
    var motions: Dictionary = character.get_motions()
    print("GODOT002_MOTIONS=", JSON.stringify(motions))
    if not motions.has("nod"):
        push_error("GODOT002_MOTION_NOD_MISSING")
        get_tree().quit(25)
        return
    character.playback_process_mode = GDCubismUserModel.IDLE
    character.start_motion("nod", 0, GDCubismUserModel.PRIORITY_FORCE)
    print("GODOT002_REAL_MOTION_STARTED")

func _process(delta: float) -> void:
    tick += delta
