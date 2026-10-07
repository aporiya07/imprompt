"""Deterministic synthetic fixtures for the structural benchmark cases.

Honest scope: these cover layout/structure cases (collages, text, low light,
product layouts). Semantic cases (portraits, couples, food...) need real photos
dropped into images/ by the operator — see README.md.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent / "images"

WARM = [(243, 214, 170), (214, 138, 74), (120, 62, 44), (248, 236, 220)]
COOL = [(168, 196, 215), (84, 110, 142), (38, 52, 74), (232, 240, 248)]


def gradient(draw: ImageDraw.ImageDraw, w: int, h: int, top, bottom):
    for y in range(h):
        t = y / max(1, h - 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        draw.line([(0, y), (w, y)], fill=color)


def photo_panel(w: int, h: int, seed: int) -> Image.Image:
    """One photo-like mini-scene: sky gradient, horizon, sun disc, figure silhouette.

    Panels share a recurring language (horizon + low warm sun + figure) with varied
    palettes/crops, so a moodboard classifier sees a real board, not abstract art.
    """
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    palettes = [
        ((250, 214, 165), (196, 110, 70)),   # golden hour
        ((214, 178, 214), (94, 70, 110)),    # dusk violet
        ((186, 214, 224), (60, 96, 118)),    # cool overcast
        ((248, 196, 150), (140, 82, 58)),    # amber
        ((200, 224, 196), (70, 104, 78)),    # green hour
    ]
    top, bottom = palettes[seed % len(palettes)]
    horizon = int(h * (0.55 + 0.08 * (seed % 3)))
    gradient(d, w, horizon, top, tuple(int(c * 0.92) for c in top))
    d.rectangle([0, horizon, w, h], fill=bottom)
    # low sun
    sr = int(min(w, h) * (0.10 + 0.03 * (seed % 2)))
    sx = int(w * (0.25 + 0.25 * (seed % 3)))
    d.ellipse([sx - sr, horizon - sr - int(h * 0.08), sx + sr, horizon + sr - int(h * 0.08)], fill=(255, 232, 190))
    # figure silhouette (rounded head + body) on the horizon
    fx = int(w * (0.35 + 0.15 * (seed % 2)))
    head_r = int(h * 0.045)
    body_w, body_h = int(w * 0.09), int(h * 0.22)
    d.ellipse([fx - head_r, horizon - body_h - 2 * head_r, fx + head_r, horizon - body_h], fill=(24, 20, 24))
    d.rounded_rectangle([fx - body_w / 2, horizon - body_h, fx + body_w / 2, horizon], radius=body_w // 3, fill=(24, 20, 24))
    return img


def collage(n_rows=3, n_cols=3):
    """Classic Pinterest moodboard: photo thumbnails separated by white gutters."""
    thumb_w, thumb_h = 300, 300
    gap = 14
    w = n_cols * thumb_w + (n_cols + 1) * gap
    h = n_rows * thumb_h + (n_rows + 1) * gap
    board = Image.new("RGB", (w, h), (248, 246, 242))
    for r in range(n_rows):
        for c in range(n_cols):
            seed = r * n_cols + c
            thumb = photo_panel(thumb_w, thumb_h, seed)
            x = gap + c * (thumb_w + gap)
            y = gap + r * (thumb_h + gap)
            board.paste(thumb, (x, y))
    return board


def text_banner():
    img = Image.new("RGB", (640, 400), (245, 242, 235))
    d = ImageDraw.Draw(img)
    d.rectangle([40, 40, 600, 360], fill=(228, 220, 205))
    d.rectangle([60, 60, 420, 130], fill=(30, 30, 34))
    try:
        font = ImageFont.load_default(size=40)
    except TypeError:
        font = ImageFont.load_default()
    d.text((76, 74), "MEGA SALE 50%", fill=(255, 255, 255), font=font)
    d.ellipse([420, 160, 590, 330], fill=(196, 60, 52))
    d.text((76, 160), "Fresh deals every day", fill=(60, 55, 50))
    return img


def low_light():
    img = Image.new("RGB", (640, 420))
    d = ImageDraw.Draw(img)
    gradient(d, 640, 420, (18, 20, 34), (44, 38, 60))
    d.ellipse([440, 40, 500, 100], fill=(210, 200, 170))  # moon
    d.rectangle([80, 260, 240, 400], fill=(30, 30, 44))  # dark building
    d.rectangle([110, 290, 140, 320], fill=(240, 210, 130))  # lit window
    return img


def product_ad():
    img = Image.new("RGB", (720, 540))
    d = ImageDraw.Draw(img)
    gradient(d, 720, 540, (250, 247, 240), (226, 216, 200))
    d.ellipse([260, 120, 460, 420], fill=(52, 92, 120))  # product bottle body
    d.rectangle([335, 60, 385, 130], fill=(230, 230, 235))  # cap
    d.ellipse([300, 160, 340, 220], fill=(240, 240, 245))  # highlight
    return img


def landscape():
    img = Image.new("RGB", (800, 450))
    d = ImageDraw.Draw(img)
    gradient(d, 800, 450, (250, 200, 140), (120, 70, 60))
    d.ellipse([600, 60, 700, 160], fill=(255, 220, 160))
    d.polygon([(0, 450), (250, 250), (500, 450)], fill=(70, 50, 55))
    d.polygon([(300, 450), (580, 210), (800, 450)], fill=(90, 60, 60))
    return img


def save(img: Image.Image, name: str):
    OUT.mkdir(parents=True, exist_ok=True)
    img.save(OUT / name, "JPEG", quality=88)
    print(f"wrote {name}")


def main():
    save(collage(3, 3), "10_pinterest_collage.jpg")
    save(collage(3, 3), "11_moodboard_3x3.jpg")
    save(text_banner(), "12_image_with_text.jpg")
    save(low_light(), "13_low_light.jpg")
    save(product_ad(), "04_product_ad.jpg")
    save(landscape(), "07_landscape.jpg")
    print("done — add real photos for the remaining categories (see README.md)")


if __name__ == "__main__":
    main()
