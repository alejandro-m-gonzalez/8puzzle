# image_utils.py — EXIF-aware slice to 3×3 and render with grid + numbers
from typing import Dict, Tuple
from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageFilter

def fix_orientation(img: Image.Image) -> Image.Image:
    try:
        return ImageOps.exif_transpose(img)
    except Exception:
        return img

def _make_blank(size: int) -> Image.Image:
    img = Image.new("RGB", (size, size), (235, 235, 235))
    d = ImageDraw.Draw(img)
    d.rectangle([0,0,size-1,size-1], outline=(160,160,160), width=3)
    step = max(8, size // 12)
    for x in range(0, size, step):
        d.line([(x,0),(0,x)], fill=(200,200,200), width=1)
    return img

def square_and_resize(img: Image.Image, target: int = 540) -> Image.Image:
    img = fix_orientation(img)
    return ImageOps.fit(img, (target, target), method=Image.Resampling.LANCZOS)

def slice_into_tiles(img: Image.Image) -> Dict[int, Image.Image]:
    size = img.size[0]
    tile = size // 3
    tiles: Dict[int, Image.Image] = {}
    k = 1
    for r in range(3):
        for c in range(3):
            box = (c*tile, r*tile, (c+1)*tile, (r+1)*tile)
            crop = img.crop(box)
            if (r, c) == (2, 2):
                tiles[0] = _make_blank(tile)
            else:
                d = ImageDraw.Draw(crop)
                d.rectangle([0,0,tile-1,tile-1], outline=(50,50,50), width=1)
                tiles[k] = crop
                k += 1
    return tiles

def _draw_centered_number(draw: ImageDraw.ImageDraw, xy: Tuple[int,int], size: int, text: str):
    # Draw larger, bolder, centered numbers with robust font fallback and outline for contrast
    # Try multiple common fonts; fall back to default if none available.
    font = None
    for name in ["DejaVuSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf", "Arial.ttf", "arial.ttf"]:
        try:
            font = ImageFont.truetype(name, size=int(size*0.58))
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()
    # Compute centered position
    bbox = draw.textbbox((0,0), text, font=font, stroke_width=4)
    tw = bbox[2]-bbox[0]; th = bbox[3]-bbox[1]
    x = xy[0] + (size - tw)//2
    y = xy[1] + (size - th)//2
    # White text with black outline for maximum legibility on any image
    draw.text((x, y), text, fill=(255,255,255), font=font, stroke_width=4, stroke_fill=(0,0,0))

def render_grid(state: Tuple[int, ...], tiles: Dict[int, Image.Image], show_numbers: bool = True, background: Image.Image = None, blur_radius: int = 6, tile_alpha: int = 255) -> Image.Image:
    tile_size = next(iter(tiles.values())).size[0]
    # Prepare base board (optional blurred background of the original image)
    if background is not None:
        bg = ImageOps.fit(background, (tile_size*3, tile_size*3), method=Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(blur_radius))
        board = bg.convert("RGBA")
    else:
        board = Image.new("RGBA", (tile_size*3, tile_size*3), (255,255,255,255))
    for i, v in enumerate(state):
        r, c = divmod(i, 3)
        tile_img = tiles[v].convert("RGBA")
        if tile_alpha < 255:
            tile_img = tile_img.copy()
            tile_img.putalpha(tile_alpha)
        board.paste(tile_img, (c*tile_size, r*tile_size), tile_img)
    d = ImageDraw.Draw(board)
    for k in range(4):
        x = k*tile_size; y = k*tile_size
        d.line([(x,0),(x,3*tile_size)], fill=(0,0,0), width=2)
        d.line([(0,y),(3*tile_size,y)], fill=(0,0,0), width=2)
    if show_numbers:
        for i, v in enumerate(state):
            if v == 0: 
                continue
            r, c = divmod(i, 3)
            _draw_centered_number(d, (c*tile_size, r*tile_size), tile_size, str(v))
    return board.convert("RGB")
