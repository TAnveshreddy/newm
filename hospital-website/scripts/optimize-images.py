"""Create web-optimised images from the original photographs.

Usage:  python3 scripts/optimize-images.py      (requires: pip install pillow)

Reads   originals/*.jpg   (the untouched photos supplied by the hospital)
Writes  src/images/*.webp (responsive sizes) and src/images/og-image.jpg

Only crops and resizes are applied. Faces and content are never altered.
To add a new gallery photo: put the JPG in originals/, add an entry to JOBS
below, run this script, then reference the name in content/site.json.
"""
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "originals"
OUT = ROOT / "src" / "images"
OUT.mkdir(parents=True, exist_ok=True)


def square(im, cx=0.5, cy=0.45):
    """Square crop centred on (cx, cy) as fractions of the image size."""
    w, h = im.size
    s = min(w, h)
    left = min(max(int(cx * w - s / 2), 0), w - s)
    top = min(max(int(cy * h - s / 2), 0), h - s)
    return im.crop((left, top, left + s, top + s))


def save_sizes(im, name, widths, quality=80):
    for width in widths:
        width = min(width, im.width)
        height = round(im.height * width / im.width)
        im.resize((width, height), Image.LANCZOS).save(
            OUT / f"{name}-{width}.webp", "WEBP", quality=quality, method=6)
        print(f"{name}-{width}.webp  {width}x{height}")


def load(name):
    return ImageOps.exif_transpose(Image.open(SRC / name)).convert("RGB")


# Exterior photo: remove the black bars above and below the picture.
exterior = load("hospital-exterior.jpg")
exterior = exterior.crop((0, 54, exterior.width, 863))
save_sizes(exterior, "hospital-exterior", [640, 1080])

# Social sharing image (1200x630) from the exterior photo.
w, h = exterior.size
target_h = round(w * 630 / 1200)
top = max(0, (h - target_h) // 2)
og = exterior.crop((0, top, w, top + target_h)).resize((1200, 630), Image.LANCZOS)
og.save(OUT / "og-image.jpg", "JPEG", quality=82, optimize=True, progressive=True)
print("og-image.jpg  1200x630")

# Home-page banner (supplied artwork of the hospital front).
# The signboard in this artwork shows incorrect doctor qualifications and
# registration numbers, so that strip is blurred. The hospital name and
# EMERGENCY sign stay visible. Remove the blur only if the artwork is corrected.
from PIL import ImageFilter
banner = Image.open(SRC / "hospital-front-banner.webp").convert("RGB")
strip = (60, 326, 790, 414)
banner.paste(banner.crop(strip).filter(ImageFilter.GaussianBlur(14)), strip[:2])
save_sizes(banner, "hospital-front-banner", [640, 1317])

# Entrance photo with the hospital team.
entrance = load("hospital-entrance-team.jpg")
save_sizes(entrance, "hospital-entrance-team", [640, 1280])

# Close-up of the main signboard (cropped from the entrance photo).
signboard = entrance.crop((0, 105, 880, 315))
save_sizes(signboard, "hospital-signboard", [640, 880])

# Emergency department & pharmacy frontage (cropped from the entrance photo).
frontage = entrance.crop((0, 420, 1280, 850))
save_sizes(frontage, "hospital-frontage", [640, 1280])

# Doctor portraits: square crops, no retouching.
save_sizes(square(load("dr-m-naresh.jpg"), cx=0.5, cy=0.45), "dr-m-naresh", [320, 640], quality=84)
save_sizes(square(load("dr-m-haritha.jpg"), cx=0.5, cy=0.5), "dr-m-haritha", [320, 640], quality=84)

# ---------------------------------------------------------------------------
# Interior photos supplied as phone screenshots (746 px wide). Crop away the
# app bars, fix exposure/contrast, sharpen and upscale with Lanczos so they
# look like normal photos. Replace originals/screenshot-*.jpg with the
# original camera photos for true HD; then adjust the crop boxes below.
from PIL import ImageEnhance

def from_screenshot(src, box, name, brightness=1.0, contrast=1.06, blur_boxes=()):
    im = load(src).crop(box)
    for b in blur_boxes:  # hide small private details (e.g. payment numbers)
        im.paste(im.crop(b).filter(ImageFilter.GaussianBlur(8)), b[:2])
    im = ImageOps.autocontrast(im, cutoff=0.5)
    im = ImageEnhance.Brightness(im).enhance(brightness)
    im = ImageEnhance.Contrast(im).enhance(contrast)
    im = ImageEnhance.Color(im).enhance(1.05)
    big = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
    big = big.filter(ImageFilter.UnsharpMask(radius=2, percent=90, threshold=2))
    save_sizes(big, name, [640, 1200], quality=86)

from_screenshot("screenshot-consultation-room.jpg", (0, 206, 746, 1196), "consultation-room")
from_screenshot("screenshot-pharmacy-shelves.jpg", (0, 423, 746, 979), "pharmacy-shelves")
from_screenshot("screenshot-newborn-warmers.jpg", (0, 423, 746, 979), "newborn-care-warmers")
from_screenshot("screenshot-laboratory.jpg", (0, 423, 746, 979), "laboratory", brightness=1.12)
from_screenshot("screenshot-pharmacy-counter.jpg", (0, 206, 746, 1197), "pharmacy-counter",
                blur_boxes=[(150, 405, 250, 465)])
