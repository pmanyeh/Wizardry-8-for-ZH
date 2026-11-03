"""Prove physical-pixel text transport against a feature-off renderer readback."""

import argparse
import json
import pathlib

import numpy as np
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('text_directory', type=pathlib.Path)
parser.add_argument('off_directory', type=pathlib.Path)
args = parser.parse_args()
root = args.text_directory
off_root = args.off_directory


def metadata(directory):
    return dict(line.split('=', 1) for line in (directory / 'render-info.txt').read_text(encoding='utf-8').splitlines() if '=' in line)


def pixels(directory, name):
    raw = np.frombuffer((directory / name).read_bytes(), dtype=np.uint8)
    assert raw.size == 1920 * 1080 * 4, f'Invalid physical buffer: {directory / name}'
    return raw.reshape(1080, 1920, 4)[:, :, [2, 1, 0, 3]]


info = metadata(root)
off_info = metadata(off_root)
assert info['phase'] == 'P1B' and info['enabled'] == '1'
assert off_info['enabled'] == '0'
assert off_info['overlay_width'] == off_info['overlay_height'] == '0', 'Disabled path allocated an overlay'
for capture_info in (info, off_info):
    assert capture_info['renderer_width'] == capture_info['readback_width'] == '1920'
    assert capture_info['renderer_height'] == capture_info['readback_height'] == '1080'
    assert capture_info['readback_ok'] == '1'
assert info['overlay_width'] == '1920' and info['overlay_height'] == '1080'
assert info['source_a_bits'] == info['texture_a_bits'] == '8'

source = pixels(root, 'source.bgra')
frame = pixels(root, 'readback.bgra')[:, :, :3]
background = pixels(off_root, 'readback.bgra')[:, :, :3]
Image.fromarray(source).save(root / 'rasterizer-output.png')
Image.fromarray(frame).save(root / 'screenshot-1920x1080.png')
Image.fromarray(background).save(off_root / 'screenshot-1920x1080.png')
alpha = source[:, :, 3].astype(np.int32)
mask = alpha > 0
assert mask.any(), 'Empty raster output'
expected = (background.astype(np.int32) * (255 - alpha[:, :, None]) +
            source[:, :, :3].astype(np.int32) * alpha[:, :, None] + 127) // 255
error = np.abs(frame.astype(np.int32) - expected)
text_error = error[mask]
max_error = text_error.max(axis=0).tolist()
bad_pixels = int(np.any(text_error > 2, axis=1).sum())
runs = []
for index in range(9):
    values = list(map(int, info[f'run_{index}'].split(',')))
    x, y, font_px, width, height, ascent, descent, missing, intermediate = values
    assert missing == 0 and intermediate > 0 and width > 0
    runs.append(dict(x=x, y=y, font_px=font_px, width=width, cell_height=height,
                     ascent=ascent, descent=descent, missing_glyphs=missing,
                     intermediate_pixels=intermediate))
assert sorted({run['font_px'] for run in runs}) == [24, 32, 48]
crop_box = (40, 342, 650, 478)
crop = Image.fromarray(frame).crop(crop_box)
crop.save(root / 'crop-1x.png')
crop.resize((crop.width * 4, crop.height * 4), Image.Resampling.NEAREST).save(root / 'crop-nearest-upscaled.png')
levels = np.unique(source[:, :, 3]).tolist()
result = {
    'status': 'PASS' if bad_pixels == 0 else 'FAIL',
    'dimensions': [1920, 1080], 'font_name': info['font_name'],
    'runs': runs, 'nontransparent_pixels': int(mask.sum()),
    'intermediate_alpha_pixels': int(((alpha > 0) & (alpha < 255)).sum()),
    'coverage_levels': levels, 'crop_1x_box': crop_box,
    'native_composite_max_rgb_error': max_error,
    'native_composite_error_limit': 2,
    'pixels_over_error_limit': bad_pixels,
    'feature_off_overlay_allocated': False,
    'proof': 'Physical-resolution GDI output is compared pixel-for-pixel with the final frame using an independent feature-off background. No intermediate 640x480 raster or resampling is used.',
}
(root / 'pixel-evidence.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps(result, indent=2, ensure_ascii=False))
raise SystemExit(bad_pixels != 0)
