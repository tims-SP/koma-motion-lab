extends Node2D

# RENDER-001: original procedural moving artwork. No third-party assets.
# Changes every frame; the validator rejects static, blank and truncated output.
var clock: float = 0.0

func _process(delta: float) -> void:
    clock += delta
    queue_redraw()

func _draw() -> void:
    var size := get_viewport_rect().size
    draw_rect(Rect2(Vector2.ZERO, size), Color("#18223d"))
    for i in range(12):
        var x := 55.0 + float(i) * 78.0
        draw_line(Vector2(x, 0.0), Vector2(x - 95.0, size.y), Color("#283856"), 3.0)
    draw_rect(Rect2(0.0, 435.0, size.x, 105.0), Color("#38536d"))
    draw_line(Vector2(0.0, 435.0), Vector2(size.x, 435.0), Color("#7ed2ce"), 6.0)

    var cx := 125.0 + 690.0 * (0.5 + 0.5 * sin(clock * 1.8))
    var cy := 235.0 + 90.0 * sin(clock * 2.6)
    var face := Vector2(cx, cy)
    draw_line(face + Vector2(-3.0, 50.0), face + Vector2(-33.0, 143.0), Color("#f9b879"), 15.0)
    draw_line(face + Vector2(4.0, 50.0), face + Vector2(49.0, 145.0), Color("#f9b879"), 15.0)
    draw_circle(face, 58.0, Color("#ffcf9c"))
    draw_circle(face + Vector2(-17.0, -8.0), 6.0, Color("#1d223e"))
    draw_circle(face + Vector2(18.0, -8.0), 6.0, Color("#1d223e"))
    draw_line(face + Vector2(-10.0, 22.0), face + Vector2(12.0, 22.0), Color("#b15e61"), 5.0)

    var hand := face + Vector2(140.0 * cos(clock * 3.3), 98.0 * sin(clock * 3.3))
    draw_line(face + Vector2(50.0, 47.0), hand, Color("#f9b879"), 17.0)
    draw_circle(hand, 13.0, Color("#ffe8bf"))
    draw_arc(face, 81.0, -0.4, 2.6 + 0.1 * sin(clock), 32, Color("#ffd47c"), 5.0)
