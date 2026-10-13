"""Cut the mascots out of the character sheets in art/ into transparent images.

Usage: python extract_mascots.py <art dir> <out dir> [--preview <dir>]
Nothing is redrawn: every output pixel comes from the sheet, only the flat panel background is removed.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

# Panel interiors (x0, x1) for the two sheet layouts, and the rows below the "1 FRONT VIEW" labels.
LAYOUT_A = {'front': (44, 399), 'profile': (425, 704), 'quarter': (733, 1007), 'rows': (170, 724)}
LAYOUT_B = {'front': (48, 353), 'profile': (379, 660), 'quarter': (688, 961), 'rows': (184, 721)}

# sheet file -> palette id, layout
SHEETS = {
    'Gemini_Generated_Image (5).jpeg': ('original', LAYOUT_A),  # Stargazer Scholar Girl
    'Gemini_Generated_Image (3).jpeg': ('midnight', LAYOUT_A),  # Researcher & Teacher
    'Gemini_Generated_Image.jpeg': ('library', LAYOUT_B),  # Archival Scholar Librarian
    'Gemini_Generated_Image (4).jpeg': ('sunset', LAYOUT_A),  # The Professor
    'Gemini_Generated_Image (1).jpeg': ('lavender', LAYOUT_A),  # Cocky Sports Star Boy
    'Gemini_Generated_Image (2).jpeg': ('forest', LAYOUT_A),  # Design-Disgust Girl Scholar
}

# Passes of (strong, faint) distance from the panel colour, see background_like(); a pixel is figure if any pass
# says so. `strong` must sit clear of every flat colour in the figure: the librarian's hair is under 20 from her
# panel, the professor's robe is 17 from his purple front panel, and the researcher's shoes are 13 from theirs
# while their tie is in the twenties, hence two passes.
VIEW_NAMES = ('front', 'quarter', 'profile')
LEVELS = {f'library/{v}': [(12, 8)] for v in VIEW_NAMES}
LEVELS |= {f'midnight/{v}': [(16, 8), (28, 6)] for v in VIEW_NAMES}
LEVELS['sunset/front'] = [(28, 9)]
DEFAULT_LEVELS = [(16, 8)]

# sheet view -> file suffix (mood slot in src/theme/mascots.ts)
VIEWS = {'front': '', 'quarter': '-wave', 'profile': '-thinking'}
PAD = 10
# Head crop: share of the figure's height that is head (sets the crop width) and how much wider to cut.
FACE = {'sunset': (0.30, 1.3)}  # the beard hangs below a head-width square
DEFAULT_FACE = (0.42, 1.06)
POCKET_MIN = 40
SIGMA = 2.0
DISK = np.hypot(*np.mgrid[-3:4, -3:4]) <= 3.2
# Enclosed gaps that are panel background rather than a dark part of the character, as a point (x, y) in the panel
# crop. Dark eyes, ties and hair partings are enclosed too, so these are listed by hand; a run prints the candidates.
POCKETS = {
    'original/quarter': [(185, 231), (142, 450)],  # lens past the cheek, between the legs
    'midnight/quarter': [(219, 161), (137, 407)],
    'library/front': [(219, 339)],  # between the pen arm and the skirt
    'library/quarter': [(141, 466)],
    'sunset/quarter': [(139, 475)],
    'lavender/quarter': [(132, 434)],
    'forest/quarter': [(142, 453)],
}


def background_like(diff: np.ndarray, strong: int, faint: float) -> np.ndarray:
    """Pixels that pass for panel background.

    Pixels further than `strong` from the panel colour are figure. The rest are averaged with their neighbours
    (leaving those out) and count as figure above `faint`, about half the contrast of the faintest shape:
    that finds dark shoes on a dark panel with a clean edge despite the JPEG noise.
    """
    solid = np.abs(diff).max(axis=2) > strong
    clean = ~ndi.binary_dilation(solid, iterations=2)  # the blended pixels along an outline would skew the average
    weight = np.maximum(ndi.gaussian_filter(clean.astype(np.float32), SIGMA), 1e-3)
    local = np.dstack([ndi.gaussian_filter(diff[..., c] * clean, SIGMA) / weight for c in range(3)])
    # Only solid faint shapes count: the opening drops the thin noisy band that follows a high-contrast outline.
    return ~solid & ~ndi.binary_opening(~solid & (np.abs(local).max(axis=2) > faint), structure=DISK)


def cut_out(panel: np.ndarray, name: str) -> np.ndarray:
    """RGBA cut-out of the figure in a panel crop: everything that does not connect to the panel edge as
    background, minus the enclosed gaps listed in POCKETS."""
    rgb = panel.astype(np.float32)
    ring = np.concatenate([rgb[:4].reshape(-1, 3), rgb[-4:].reshape(-1, 3), rgb[:, :4].reshape(-1, 3), rgb[:, -4:].reshape(-1, 3)])
    diff = rgb - np.median(ring, axis=0)
    near_bg = np.logical_and.reduce([background_like(diff, *levels) for levels in LEVELS.get(name, DEFAULT_LEVELS)])

    labels, n = ndi.label(near_bg)
    edge = np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
    background = np.isin(labels, edge[edge > 0])

    figure = ~background
    parts, m = ndi.label(figure)
    if m > 1:  # drop label text and specks, keep the character
        sizes = ndi.sum(figure, parts, range(1, m + 1))
        figure = parts == (1 + int(np.argmax(sizes)))

    # Gaps the outside cannot reach (between the legs, behind a lens that overhangs the face).
    sizes = ndi.sum(near_bg, labels, range(1, n + 1))
    for i, (size, sl) in enumerate(zip(sizes, ndi.find_objects(labels)), start=1):
        if size < POCKET_MIN or i in edge:
            continue
        hit = any(sl[1].start <= x < sl[1].stop and sl[0].start <= y < sl[0].stop for x, y in POCKETS.get(name, ()))
        print(f'    {"pocket " if hit else "enclosed"} {name}: {int(size)}px at x{sl[1].start}-{sl[1].stop} y{sl[0].start}-{sl[0].stop}')
        if hit:
            figure[labels == i] = False

    # The outer two pixels are blended with the dark panel: give them the colour just inside and soften the edge.
    # Lines too thin to have an inside (glasses, the pen) keep their own colour.
    core = ndi.binary_erosion(figure, iterations=2)
    dist, (iy, ix) = ndi.distance_transform_edt(~core, return_indices=True)
    blended = figure & ~core & (dist < 3)
    colour = np.where(blended[..., None], panel[iy, ix], panel)
    alpha = np.clip(ndi.gaussian_filter(figure.astype(np.float32), 0.7), 0, 1) * figure * 255
    return np.dstack([colour, alpha]).astype(np.uint8)


def bbox(alpha: np.ndarray, level: int = 8):
    ys, xs = np.where(alpha > level)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def squared(rgba: np.ndarray) -> Image.Image:
    """Trim to the figure and centre it on a transparent square."""
    x0, y0, x1, y1 = bbox(rgba[..., 3])
    fig = Image.fromarray(rgba[y0:y1, x0:x1], 'RGBA')
    side = max(fig.size) + 2 * PAD
    out = Image.new('RGBA', (side, side), (0, 0, 0, 0))
    out.paste(fig, ((side - fig.width) // 2, (side - fig.height) // 2))
    return out


def face(rgba: np.ndarray, head: float, scale: float) -> Image.Image:
    """Head-and-shoulders square for avatar sizes, where a full figure would be a few pixels wide."""
    x0, y0, x1, y1 = bbox(rgba[..., 3])
    h = y1 - y0
    top = rgba[y0 : y0 + int(h * head), :, 3] > 8
    cols = np.where(top.any(axis=0))[0]
    side = int((cols.max() - cols.min() + 1) * scale)
    cx = (cols.min() + cols.max() + 1) // 2
    left = cx - side // 2
    canvas = Image.new('RGBA', (side, side), (0, 0, 0, 0))
    src = Image.fromarray(rgba, 'RGBA').crop((left, y0 - 4, left + side, y0 - 4 + side))
    canvas.paste(src, (0, 0))
    return canvas


def main() -> None:
    art, out = Path(sys.argv[1]), Path(sys.argv[2])
    preview = Path(sys.argv[sys.argv.index('--preview') + 1]) if '--preview' in sys.argv else None
    out.mkdir(parents=True, exist_ok=True)
    for name, (palette, layout) in SHEETS.items():
        sheet = np.asarray(Image.open(art / name).convert('RGB'))
        r0, r1 = layout['rows']
        made = {}
        for view, suffix in VIEWS.items():
            c0, c1 = layout[view]
            rgba = cut_out(sheet[r0:r1, c0:c1], f'{palette}/{view}')
            made[suffix] = squared(rgba)
            if view == 'front':
                made['-face'] = face(rgba, *FACE.get(palette, DEFAULT_FACE))
        for suffix, img in made.items():
            img.save(out / f'{palette}{suffix}.webp', 'WEBP', lossless=True, method=6)
        if preview:
            preview.mkdir(parents=True, exist_ok=True)
            for tone, colour in (('light', (241, 248, 255)), ('dark', (20, 24, 34)), ('pink', (255, 0, 200))):
                strip = Image.new('RGB', (4 * 420, 420), colour)
                for i, img in enumerate(made.values()):
                    tile = img.resize((400, 400), Image.LANCZOS)
                    strip.paste(tile, (i * 420 + 10, 10), tile)
                strip.save(preview / f'{palette}-{tone}.png')
        print(palette, {k or 'idle': v.size for k, v in made.items()})


if __name__ == '__main__':
    main()
