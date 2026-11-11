"""Film-look grade shared by previews and the final edit (numpy, uint8 RGB in/out).
Bloom on highlights, teal shadows / warm highlights, gentle S-curve, vignette, grain.
"""
import numpy as np

try:
    import cv2
except Exception:  # cv2 is optional for previews
    cv2 = None


def _blur(x, sigma):
    if cv2 is not None:
        return cv2.GaussianBlur(x, (0, 0), sigma)
    from PIL import Image, ImageFilter
    out = np.empty_like(x)
    for c in range(3):
        im = Image.fromarray(np.clip(x[..., c] * 255, 0, 255).astype(np.uint8))
        out[..., c] = np.asarray(im.filter(ImageFilter.GaussianBlur(sigma))) / 255.0
    return out


def grade(img, seed=0, bloom=0.22, vignette=0.38, grain=0.02, sat=1.05,
          shadow_tint=(-0.012, 0.004, 0.022), high_tint=(0.018, 0.006, -0.012)):
    x = img.astype(np.float32) / 255.0
    h, w = x.shape[:2]
    # bloom: only what is already bright (screens, tube, moon shafts)
    lum = x @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    hi = np.clip((lum - 0.62) / 0.38, 0, 1)[..., None] * x
    s = max(h, w) / 1920
    b = _blur(hi, 6 * s) * 0.5 + _blur(hi, 24 * s) * 0.5
    x = x + b * bloom
    # split tone
    lum = x @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    ws = np.clip(1 - lum * 2, 0, 1)[..., None]
    wh = np.clip(lum * 2 - 1, 0, 1)[..., None]
    x = x + ws * np.array(shadow_tint, np.float32) + wh * np.array(high_tint, np.float32)
    # saturation
    g = (x @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
    x = g + (x - g) * sat
    # soft S-curve with lifted blacks (film, not crushed game blacks)
    x = np.clip(x, 0, 1)
    x = x * x * (3 - 2 * x) * 0.35 + x * 0.65
    x = 0.018 + x * (1 - 0.018)
    # vignette
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / np.sqrt(2)
    x *= (1 - vignette * np.clip(r - 0.25, 0, 1) ** 1.6)[..., None]
    # luminance grain (stronger in mids)
    rng = np.random.default_rng(seed)
    n = rng.standard_normal((h, w)).astype(np.float32)
    n = _blur(np.repeat(n[..., None], 3, -1), 0.6 * s + 0.01)[..., :1] * 1.6
    lum = x.mean(-1, keepdims=True)
    x += n * grain * (0.4 + 0.6 * (1 - np.abs(lum * 2 - 1)))
    return (np.clip(x, 0, 1) * 255).astype(np.uint8)


if __name__ == "__main__":
    import sys
    from PIL import Image
    for p in sys.argv[1:]:
        a = np.asarray(Image.open(p).convert("RGB"))
        Image.fromarray(grade(a)).save(p)
