#!/usr/bin/env python3
"""Generate a cool N64/Zelda-themed desktop icon."""

import os
from PIL import Image, ImageDraw, ImageFont

SIZE = 256
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(OUTPUT_DIR, "n64_icon.png")
ICO_PATH = os.path.join(OUTPUT_DIR, "n64_icon.ico")


def draw_n64_controller(draw, cx, cy, scale=1.0):
    """Draw a simplified N64 controller silhouette."""
    # Main body shape — a rounded trapezoid
    body_w = int(140 * scale)
    body_h = int(90 * scale)
    left = cx - body_w // 2
    top = cy - body_h // 2

    # Controller body (dark gray)
    draw.pieslice(
        [left, top, left + body_w, top + body_h],
        start=0, end=360, fill="#3a3a3a"
    )
    # Grip (left)
    draw.rectangle(
        [left - int(20 * scale), top + int(10 * scale),
         left - int(8 * scale), top + body_h - int(10 * scale)],
        fill="#3a3a3a"
    )
    # Grip (right)
    draw.rectangle(
        [left + body_w + int(8 * scale), top + int(10 * scale),
         left + body_w + int(20 * scale), top + body_h - int(10 * scale)],
        fill="#3a3a3a"
    )

    # D-Pad (left side)
    dpad_x = left + int(25 * scale)
    dpad_y = cy
    dpad_w = int(20 * scale)
    dpad_h = int(40 * scale)
    draw.rectangle(
        [dpad_x - dpad_w // 2, dpad_y - dpad_h // 2,
         dpad_x + dpad_w // 2, dpad_y + dpad_h // 2],
        fill="#1a1a1a"
    )
    draw.rectangle(
        [dpad_x - dpad_h // 2, dpad_y - dpad_w // 2,
         dpad_x + dpad_h // 2, dpad_y + dpad_w // 2],
        fill="#1a1a1a"
    )

    # A Button (right side — green) — N64 layout has green A
    btn_a_x = left + body_w - int(30 * scale)
    btn_a_y = cy - int(5 * scale)
    btn_r = int(10 * scale)
    draw.ellipse(
        [btn_a_x - btn_r, btn_a_y - btn_r,
         btn_a_x + btn_r, btn_a_y + btn_r],
        fill="#00cc66", outline="#009944", width=2
    )
    # A label
    draw.text((btn_a_x - 4, btn_a_y - 5), "A", fill="white")

    # B Button (left of A — yellow/red) — N64 has yellow B
    btn_b_x = btn_a_x - int(22 * scale)
    btn_b_y = cy + int(5 * scale)
    draw.ellipse(
        [btn_b_x - btn_r, btn_b_y - btn_r,
         btn_b_x + btn_r, btn_b_y + btn_r],
        fill="#ffcc00", outline="#cc9900", width=2
    )
    draw.text((btn_b_x - 4, btn_b_y - 5), "B", fill="black")

    # C-buttons (right cluster — yellow)
    c_cx = left + body_w - int(10 * scale)
    c_cy = cy - int(20 * scale)
    c_r = int(5 * scale)
    for dx, dy in [(0, -10), (0, 10), (-10, 0), (10, 0)]:
        draw.ellipse(
            [c_cx + dx - c_r, c_cy + dy - c_r,
             c_cx + dx + c_r, c_cy + dy + c_r],
            fill="#ffdd00", outline="#ccaa00"
        )

    # Start button (center)
    start_x = cx
    start_y = top + body_h - int(15 * scale)
    draw.ellipse(
        [start_x - int(8 * scale), start_y - int(5 * scale),
         start_x + int(8 * scale), start_y + int(5 * scale)],
        fill="#555555"
    )

    return draw


def draw_triforce(draw, cx, cy, size=40):
    """Draw a golden Triforce symbol."""
    s = size
    h = s * 0.866  # height of equilateral triangle

    # Top triangle
    top_pts = [
        (cx, cy - h * 0.7),
        (cx - s * 0.5, cy + h * 0.3),
        (cx + s * 0.5, cy + h * 0.3),
    ]
    draw.polygon(top_pts, fill="#ffd700", outline="#b8960c", width=2)

    # Bottom-left triangle
    bl_pts = [
        (cx - s * 0.5, cy + h * 0.3),
        (cx - s * 0.25, cy + h * 0.3),
        (cx - s * 0.25, cy - h * 0.05),
    ]
    draw.polygon(bl_pts, fill="#ffd700", outline="#b8960c", width=1)

    # Bottom-right triangle
    br_pts = [
        (cx + s * 0.5, cy + h * 0.3),
        (cx + s * 0.25, cy + h * 0.3),
        (cx + s * 0.25, cy - h * 0.05),
    ]
    draw.polygon(br_pts, fill="#ffd700", outline="#b8960c", width=1)

    return draw


def generate_icon():
    """Generate the full desktop icon."""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background circle with gradient feel (dark navy)
    bg_radius = SIZE // 2 - 8
    bg_cx = SIZE // 2
    bg_cy = SIZE // 2

    # Outer glow ring
    for r in range(bg_radius, bg_radius - 20, -1):
        alpha = int(30 * (1 - (bg_radius - r) / 20))
        draw.ellipse(
            [bg_cx - r, bg_cy - r, bg_cx + r, bg_cy + r],
            fill=(30, 40, 80, alpha)
        )

    # Main background circle
    draw.ellipse(
        [bg_cx - bg_radius + 8, bg_cy - bg_radius + 8,
         bg_cx + bg_radius - 8, bg_cy + bg_radius - 8],
        fill="#1a1a2e"
    )

    # Inner subtle ring
    inner_r = bg_radius - 25
    draw.ellipse(
        [bg_cx - inner_r, bg_cy - inner_r,
         bg_cx + inner_r, bg_cy + inner_r],
        outline="#2a2a4e", width=2
    )

    # Draw the N64 controller
    draw_n64_controller(draw, bg_cx - 10, bg_cy + 15, scale=1.0)

    # Draw Triforce above the controller
    draw_triforce(draw, bg_cx + 50, bg_cy - 35, size=30)

    # Star-like accents
    for x, y in [(bg_cx - 70, bg_cy - 50), (bg_cx + 70, bg_cy - 60),
                 (bg_cx - 60, bg_cy + 40), (bg_cx + 65, bg_cy + 35)]:
        draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill="#e94560")

    # Save as PNG
    img.save(ICON_PATH, "PNG")
    print(f"  ✅  Icon PNG saved: {ICON_PATH} ({os.path.getsize(ICON_PATH)} bytes)")

    # Save as ICO (multiple sizes)
    img_256 = img
    # Create ICO with multiple sizes for Windows
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    imgs = []
    for size in icon_sizes:
        resized = img.resize(size, Image.LANCZOS)
        imgs.append(resized)
    imgs[0].save(
        ICO_PATH, "ICO", sizes=icon_sizes, append_images=imgs[1:]
    )
    print(f"  ✅  Icon ICO saved: {ICO_PATH} ({os.path.getsize(ICO_PATH)} bytes)")

    return ICON_PATH, ICO_PATH


if __name__ == "__main__":
    generate_icon()
