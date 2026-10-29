extends Node2D

var character: GDCubismUserModel
var tick: float = 0.0

func _ready() -> void:
    character = GDCubismUserModel.new()
    add_child(character)
    character.assets = "res://assets/301003_x/301003_x.model3.json"
    var canvas: Dictionary = character.get_canvas_info()
    if canvas.is_empty() or not canvas.has("size_in_pixels"):
        push_error("GODOT002_MODEL_LOAD_FAILED")
        get_tree().quit(24)
        return
    var dims: Vector2 = canvas["size_in_pixels"]
    var factor: float = min(750.0 / max(dims.x, 1.0), 495.0 / max(dims.y, 1.0))
    character.position = Vector2(480, 270)
    character.scale = Vector2.ONE * factor
    print("GODOT002_MODEL_CANVAS=", dims, " SCALE=", factor)
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
