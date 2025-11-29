#!/usr/bin/env python3
"""
Favicon Generator for Epstein Archive
Creates island + plane favicon in multiple sizes
"""

import os

from PIL import Image, ImageDraw


def create_island_plane_favicon(size):
    """
    Create a favicon with a tropical island and plane.

    Design elements:
    - Sky gradient (top)
    - Ocean (bottom half)
    - Small island with palm tree
    - Plane flying overhead
    """
    # Create image with sky background
    img = Image.new("RGB", (size, size), "#4A90E2")
    draw = ImageDraw.Draw(img)

    # Draw ocean (bottom 60% for better composition)
    ocean_color = "#2E5C8A"
    ocean_start = int(size * 0.4)
    draw.rectangle([(0, ocean_start), (size, size)], fill=ocean_color)

    # Draw island (ellipse in lower center)
    island_color = "#6B8E23"
    island_x = size // 2
    island_y = int(size * 0.72)
    island_radius_x = int(size * 0.22)
    island_radius_y = int(size * 0.12)

    draw.ellipse(
        [
            (island_x - island_radius_x, island_y - island_radius_y),
            (island_x + island_radius_x, island_y + island_radius_y),
        ],
        fill=island_color,
    )

    # Draw beach sand (lighter strip on top of island)
    if size >= 32:
        sand_color = "#DEB887"
        draw.ellipse(
            [
                (island_x - island_radius_x + 2, island_y - island_radius_y - 1),
                (island_x + island_radius_x - 2, island_y - 2),
            ],
            fill=sand_color,
        )

    # Draw palm tree (only if size >= 32 for visibility)
    if size >= 32:
        palm_trunk_color = "#8B4513"
        palm_leaves_color = "#2F4F2F"

        # Palm tree positioned on island
        palm_x = island_x + int(island_radius_x * 0.4)
        palm_y = island_y - int(island_radius_y * 0.8)

        # Trunk (thin rectangle)
        trunk_width = max(2, size // 64)
        trunk_height = int(size * 0.12)
        draw.rectangle(
            [
                (palm_x - trunk_width // 2, palm_y - trunk_height),
                (palm_x + trunk_width // 2, palm_y),
            ],
            fill=palm_trunk_color,
        )

        # Leaves (triangle)
        leaf_size = int(size * 0.08)
        draw.polygon(
            [
                (palm_x, palm_y - trunk_height - leaf_size),
                (palm_x - leaf_size, palm_y - trunk_height + 2),
                (palm_x + leaf_size, palm_y - trunk_height + 2),
            ],
            fill=palm_leaves_color,
        )

    # Draw plane (white silhouette in upper portion)
    plane_color = "#FFFFFF"
    plane_x = int(size * 0.28)
    plane_y = int(size * 0.25)
    plane_length = int(size * 0.25)
    plane_wing_span = int(size * 0.12)

    # Plane body (main fuselage - horizontal wedge)
    draw.polygon(
        [
            (plane_x, plane_y),
            (plane_x + plane_length, plane_y - 2),
            (plane_x + plane_length, plane_y + 2),
        ],
        fill=plane_color,
    )

    # Wings (perpendicular line)
    wing_x = plane_x + int(plane_length * 0.4)
    draw.polygon(
        [
            (wing_x, plane_y - plane_wing_span // 2),
            (wing_x + 2, plane_y - plane_wing_span // 2),
            (wing_x + 2, plane_y + plane_wing_span // 2),
            (wing_x, plane_y + plane_wing_span // 2),
        ],
        fill=plane_color,
    )

    # Tail (small triangle at back)
    if size >= 32:
        tail_x = plane_x + plane_length
        tail_size = int(size * 0.06)
        draw.polygon(
            [
                (tail_x, plane_y),
                (tail_x - tail_size // 2, plane_y - tail_size),
                (tail_x + 2, plane_y),
            ],
            fill=plane_color,
        )

    return img


def generate_all_favicons(output_dir):
    """Generate all required favicon sizes"""

    os.makedirs(output_dir, exist_ok=True)

    # Size specifications
    favicon_sizes = {
        16: "favicon-16x16.png",
        32: "favicon-32x32.png",
        48: "favicon-48x48.png",
        64: "favicon-64x64.png",
        180: "apple-touch-icon.png",
        192: "android-chrome-192x192.png",
        512: "android-chrome-512x512.png",
    }

    print("Generating favicon images...")

    # Generate PNG files
    ico_images = []
    for size, filename in favicon_sizes.items():
        print(f"  Creating {filename} ({size}x{size})")
        img = create_island_plane_favicon(size)
        filepath = os.path.join(output_dir, filename)
        img.save(filepath, "PNG")

        # Collect images for ICO file (16, 32, 48)
        if size in [16, 32, 48]:
            ico_images.append((img, size))

    # Create multi-resolution favicon.ico
    print("  Creating favicon.ico (multi-resolution)")
    ico_path = os.path.join(output_dir, "favicon.ico")

    # Sort by size and extract images
    ico_images.sort(key=lambda x: x[1])
    images = [img for img, _ in ico_images]

    # Save as ICO with multiple sizes
    images[0].save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])

    print(f"\n✓ All favicon files created in: {output_dir}")
    return True


def create_webmanifest(output_dir):
    """Create site.webmanifest file"""

    manifest_content = """{
    "name": "Epstein Archive",
    "short_name": "Epstein Archive",
    "icons": [
        {
            "src": "/android-chrome-192x192.png",
            "sizes": "192x192",
            "type": "image/png"
        },
        {
            "src": "/android-chrome-512x512.png",
            "sizes": "512x512",
            "type": "image/png"
        }
    ],
    "theme_color": "#2E5C8A",
    "background_color": "#4A90E2",
    "display": "standalone"
}
"""

    manifest_path = os.path.join(output_dir, "site.webmanifest")
    with open(manifest_path, "w") as f:
        f.write(manifest_content)

    print("✓ Created site.webmanifest")
    return True


if __name__ == "__main__":
    # Output directory
    output_dir = os.path.join(os.path.dirname(__file__), "web")

    print("=" * 60)
    print("Epstein Archive Favicon Generator")
    print("=" * 60)

    # Generate favicons
    generate_all_favicons(output_dir)

    # Create webmanifest
    create_webmanifest(output_dir)

    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("Add these lines to server/web/index.html in the <head> section:")
    print("")
    print('<link rel="icon" type="image/x-icon" href="/favicon.ico">')
    print('<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">')
    print('<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">')
    print('<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">')
    print('<link rel="manifest" href="/site.webmanifest">')
    print("")
    print("=" * 60)
