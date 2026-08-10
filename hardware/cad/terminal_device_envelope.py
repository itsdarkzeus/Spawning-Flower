"""Representative envelope for the Hikvision DS-K1A8503MF-B terminal.

NOT A VENDOR MODEL. Hikvision does not publish a STEP file for this SKU and the
step.parts catalog has no match (searched: "Hikvision fingerprint terminal",
"access control terminal" - both returned 0 results against a reachable API).

This is a documented envelope built only from the published outline
(140 x 155 x 30 mm) plus approximate front-face features, so the assembly has
something to mount and so clearances can be seen. Screen and sensor positions
are indicative and are NOT dimensions to design against - only the outer
140 x 155 x 30 envelope is sourced.

Coordinate convention
    Origin : centre of the bottom edge of the wall-facing face
    X      : horizontal, across the wall
    +Y     : away from the wall, towards the room
    +Z     : up
"""

from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    Circle,
    Locations,
    Mode,
    Plane,
    RectangleRounded,
    extrude,
    fillet,
)

from cadpy.assembly import label_shape

# --- Published envelope -----------------------------------------------------
body_w = 140.0
body_h = 155.0
body_d = 30.0

corner_r = 4.0

# --- Indicative front-face features (NOT sourced dimensions) ----------------
screen_w = 52.0
screen_h = 40.0
screen_z = 108.0
screen_depth = 1.2

sensor_w = 26.0
sensor_h = 22.0
sensor_z = 46.0
sensor_depth = 1.5

card_field_d = 34.0
card_field_z = 78.0
card_field_depth = 0.6

cut_overshoot = 1.0


def make_device():
    with BuildPart() as device:
        Box(
            body_w,
            body_d,
            body_h,
            align=(Align.CENTER, Align.MIN, Align.MIN),
        )
        fillet(device.edges().filter_by(Axis.Z), corner_r)

        front = Plane.XZ.offset(-(body_d + cut_overshoot))

        # Screen recess
        with BuildSketch(front):
            with Locations((0.0, screen_z)):
                RectangleRounded(screen_w, screen_h, 2.0)
        extrude(amount=screen_depth + cut_overshoot, mode=Mode.SUBTRACT)

        # Card read field
        with BuildSketch(front):
            with Locations((0.0, card_field_z)):
                Circle(card_field_d / 2.0)
        extrude(amount=card_field_depth + cut_overshoot, mode=Mode.SUBTRACT)

        # Fingerprint sensor recess
        with BuildSketch(front):
            with Locations((0.0, sensor_z)):
                RectangleRounded(sensor_w, sensor_h, 6.0)
        extrude(amount=sensor_depth + cut_overshoot, mode=Mode.SUBTRACT)

    return device.part


def gen_step():
    return label_shape(make_device(), "terminal_device_envelope")


if __name__ == "__main__":
    gen_step()
