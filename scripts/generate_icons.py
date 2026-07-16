"""Generate Android/PWA raster icons from the NavalForge visual system."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1] / "frontend" / "public" / "icons"


def icon(size: int, maskable: bool = False) -> Image.Image:
    image = Image.new("RGB", (size, size), "#082632")
    draw = ImageDraw.Draw(image)
    inset = int(size * (0.20 if maskable else 0.14))
    center = size // 2
    diamond = [(center, inset), (size - inset, center), (center, size - inset), (inset, center)]
    draw.line(diamond + [diamond[0]], fill="#45d6dc", width=max(5, size // 24), joint="curve")
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", int(size * 0.31))
    except OSError:
        font = ImageFont.load_default()
    box = draw.textbbox((0, 0), "NF", font=font)
    text_width = box[2] - box[0]
    text_height = box[3] - box[1]
    draw.text(
        ((size - text_width) / 2, center - text_height * 0.72),
        "NF",
        font=font,
        fill="#edfafa",
    )
    points = [
        (int(size * 0.23), int(size * 0.66)),
        (int(size * 0.39), int(size * 0.62)),
        (int(size * 0.55), int(size * 0.65)),
        (int(size * 0.72), int(size * 0.63)),
        (int(size * 0.79), int(size * 0.61)),
    ]
    draw.line(points, fill="#3fd4dd", width=max(4, size // 31), joint="curve")
    return image


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    icon(192).save(ROOT / "icon-192.png", optimize=True)
    icon(512).save(ROOT / "icon-512.png", optimize=True)
    icon(512, maskable=True).save(ROOT / "icon-maskable-512.png", optimize=True)
    print("PWA icons generated")


if __name__ == "__main__":
    main()
